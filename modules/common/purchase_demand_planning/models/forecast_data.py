    # -*- coding: utf-8 -*-
import itertools
import logging
import math
import sys
from datetime import datetime

import pytz
from dateutil.relativedelta import relativedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
import matplotlib.pyplot as plt
import seaborn as sns
import sklearn.metrics
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.seasonal import seasonal_decompose
import pandas as pd
import pmdarima as pmd


from odoo import models, fields, api, _
from odoo.exceptions import UserError, MissingError

_log = logging.getLogger(__name__)


VTABLE_QUERY = """
select 'mfg' ftype, stock_move.product_id, stock_move.date, stock_move.product_uom_qty 
from stock_move
join stock_location on (stock_move.location_dest_id = stock_location.id )
where stock_move.state != 'cancel' 
and stock_move.company_id = %(cid)s 
and stock_move.date between %(expected)s and current_timestamp 
and stock_location.usage = 'production' 
union
select 'mfg' ftype, stock_move.product_id, stock_move.date, -stock_move.product_uom_qty 
from stock_move
join stock_location on (stock_move.location_id = stock_location.id )
where stock_move.state != 'cancel' 
and stock_move.company_id = %(cid)s 
and stock_move.date between %(expected)s and current_timestamp 
and stock_location.usage = 'production'
union 
select 'sale' ftype, stock_move.product_id, stock_move.date, stock_move.product_uom_qty 
from stock_move
join stock_location on (stock_move.location_dest_id = stock_location.id )
where stock_move.state != 'cancel' 
and stock_move.company_id = %(cid)s 
and stock_move.date between %(expected)s and current_timestamp 
and stock_location.usage = 'customer' 
union 
select 'sale' ftype, stock_move.product_id, stock_move.date, -stock_move.product_uom_qty 
from stock_move
join stock_location on (stock_move.location_id = stock_location.id )
where stock_move.state != 'cancel' 
and stock_move.company_id = %(cid)s 
and stock_move.date between %(expected)s and current_timestamp 
and stock_location.usage = 'customer'
"""


class ProductPeriod:
    def __init__(self, line, reference):
        self.line = line

        self.periods = {}
        if line.forecast_data.plot_type:
            for ptype in ["sale", "mfg"]:
                for k in reference:
                    mon, year = k
                    self.periods[(ptype, mon, year)] = None
        else:
            for k in reference:
                mon, year = k
                self.periods[("sale", mon, year)] = None


class ForecastData(models.Model):
    _name = "forecast.data"
    _order = "id desc"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    @api.model
    def _get_sequence(self):
        value = self.env.get("ir.sequence").next_by_code("forecast.data")
        return value

    ################################################################################
    # Fields
    ################################################################################
    name = fields.Char(string="Reference", default=_get_sequence, required=True)
    company = fields.Many2one("res.company", required=True, default=lambda self: self.env.company)
    generated = fields.Datetime(string="Forecasted On", readonly=True)
    state = fields.Selection(
        string="State",
        selection=[
            ("draft", "Draft"),
            ("open", "Open"),
            ("closed", "Done"),
        ],
        required=True,
        default="draft",
    )
    # Generation parameters
    product_categories = fields.Many2many(comodel_name="product.category", string="Product Categories")
    supplier = fields.Many2one(
        "res.partner",
        string="Set Supplier",
        domain=[("supplier_rank", ">", 0), ("is_company", "=", True)],
        help="If used, if this supplier is a supplier for a selected product they will be populated on that line, otherwise left blank",
    )
    lines = fields.One2many("forecast.data.line", "forecast_data", string="Lines")
    history_count = fields.Integer(
        string="Demand History Months", required=True, default=lambda self: self.env.company.history_count
    )
    forecast_count = fields.Integer(
        string="Forecast Months", required=True, default=lambda self: self.env.company.forecast_count
    )
    plot_type = fields.Boolean(
        string="Plot Sale Demand Separate From Production Demand", default=lambda self: self.env.company.plot_type
    )
    forecast_from = fields.Selection(
        string="Forecast From",
        selection=[("this_month", "Current Month"), ("next_month", "Next Month")],
        default="next_month",
    )

    ###########################################################################
    # Model methods
    ###########################################################################

    def unlink(self):
        for rec in self:
            if [line for line in rec.lines if line.purchase or line.manufacturing]:
                raise UserError("You cannot delete a forecast linked to Purchase or Manufacturing orders")

        return super(ForecastData, self).unlink()

    def button_set_done(self):
        self.write({"state": "closed"})

    def button_purchase_create(self):
        """
        Bring up wizard to review purchase.
        """
        self.ensure_one()

        wizard = self.env["forecast.generate.purchase"].create_wizard(self)
        return {
            "name": wizard._description,
            "view_mode": "form",
            "view_type": "form",
            "res_model": wizard._name,
            "res_id": wizard.id,
            "type": "ir.actions.act_window",
            "nodestroy": False,
            "target": "new",
        }

    def _determine_start(self):

        back = datetime.now() - relativedelta(months=self.history_count)
        return fields.Datetime.to_string(back)

    def _button_generate_forecast(self):
        """Generate the forecast lines."""
        # Sanity checks
        if self.forecast_count <= 0:
            raise UserError("Invalid Forecast Count")
        if self.history_count < 1:
            raise UserError("Invalid History Count")

        product_periods = self.build_product_history()
        self.build_forecast(product_periods)


        internals = self.env["stock.location"].search(
            [
                ("company_id", "=", self.company.id),
                ("usage", "=", "internal"),
            ]
        )
        for pp in product_periods.values():
            pp.line.update_quantities(internals)

        self.write(
            {
                "state": "open",
                "generated": fields.Datetime.now(),
            }
        )


    def build_product_history(self):
        """
        Build historical data.

        :param rows: sql query results
        :return: map of {product.id: ProductPeriod(line, periods)}
        """
        line_model = self.env["forecast.data.line"]
        plot_model = self.env["forecast.data.plot"]

        product_periods = {}
        reference = self.get_reference_periods()
        for row in self.get_product_consumption_rows():

            ptype = row[0]
            product_id = row[1]
            year = row[2]
            month = row[3]
            quantity = row[4]

            if product_id in product_periods:
                pp = product_periods[product_id]
            else:
                line = line_model.create(
                    {
                        "forecast_data": self.id,
                        "product": product_id,
                        "method": "periodic",
                        "supplierinfo": self.get_product_supplier_info(product_id),
                    }
                )
                _log.debug("created forecast.data.line product={}".format(product_id))
                pp = ProductPeriod(line, reference)
                product_periods[product_id] = pp

            plot = plot_model.create(
                {
                    "forecast_line": pp.line.id,
                    "type": ptype,
                    "year": year,
                    "month": month,
                    "forecast": 0,
                    "actual": quantity,
                    "actual_forecast": quantity,
                }
            )

            pp.periods[(ptype, month, year)] = plot

        # Backfill missing periods with zero-qty
        for product_id, product_period in product_periods.items():
            pperiods = dict(product_period.periods)  # use a copy for inspection
            for key, plot in pperiods.items():
                if plot:
                    continue
                ptype, month, year = key
                plot = plot_model.create(
                    {
                        "forecast_line": product_period.line.id,
                        "type": ptype,
                        "year": year,
                        "month": month,
                        "forecast": 0,
                        "actual": 0,
                        "actual_forecast": 0,
                    }
                )
                product_period.periods[key] = plot
        return product_periods

    def get_product_consumption_rows(self):
        """Get all the product consumption rows from the DB."""
        params = {
            "cid": self.company.id,
            "expected": self._determine_start(),
        }

        product_expression, product_ids = self.get_products_expression_and_products()
        if product_ids:
            params["pid"] = tuple(product_ids)
        if self.plot_type:
            sql = (
                "select ftype, product_id, extract (year from date) as year, "
                "extract (month from date) as month, sum (product_uom_qty) as qty, product_template.name "
                "from ({vtable}) as history, product_product, product_template "
                "where {pid_expr} product_product.id = product_id and product_template.id = product_tmpl_id "
                "group by ftype, product_id, year, month, product_template.name "
                "order by product_template.name"
            ).format(pid_expr=product_expression, vtable=VTABLE_QUERY)
        else:
            sql = (
                "select 'sale', product_id, extract (year from date) as year, "
                "extract (month from date) as month, sum (product_uom_qty) as qty, product_template.name "
                "from ({vtable}) as history, product_product, product_template "
                "where {pid_expr} product_product.id = product_id and product_template.id = product_tmpl_id "
                "group by product_id, year, month, product_template.name "
                "order by product_template.name"
            ).format(pid_expr=product_expression, vtable=VTABLE_QUERY)

        self.env.cr.execute(sql, params)
        product_rows = self.env.cr.fetchall()
        _log.info(f"get_product_consumption_rows - product row count: {len(product_rows)}")
        return product_rows

    def get_products_expression_and_products(self):
        """Get a list of product ids matching selected categories."""
        if self.product_categories:
            products = self.get_products_for_categories(self.product_categories)
            _log.info(f"get_all_products_from_categories product count: {len(products)}")
            return "product_id in %(pid)s and ", list(products)
        else:
            supplier_products = self.get_product_for_suppliers(self.supplier)
            if supplier_products:
                _log.info(f"get_all_products_for_suppliers product count: {len(supplier_products)}")
                return "product_id in %(pid)s and ", list(supplier_products)
            else:
                _log.warning("No Products Found For this Supplier {}".format(self.supplier.display_name))
                raise UserError("No Products Found For this Supplier!".format(self.supplier.display_name))

    def get_products_for_categories(self, categories):
        """
        Return set of product ids from categories, recursively.
        :return:
        """
        product_model = self.env["product.product"]
        category_model = self.env["product.category"]

        ids = set()
        for cat in categories:
            ids.update(product_model.search([("categ_id", "=", cat.id)]).ids)
            children = category_model.search([("parent_id", "=", cat.id)])
            if children:
                ids.update(self.get_products_for_categories(children))

        return ids

    def get_product_for_suppliers(self, supplier):
        """
        Return set of product ids linked to the supplier.
        :return:
        """
        if not supplier:
            return set()

        product_supplierinfo_model = self.env["product.supplierinfo"]
        supplierinfo_records = product_supplierinfo_model.search([("partner_id", "=", supplier.id)])

        if supplierinfo_records:
            product_ids = set(supplierinfo_records.mapped('product_tmpl_id').ids)
            return product_ids



    def get_reference_periods(self):
        """Get reference periods.
        :return: A list of years and months for the history back count.
        """
        periodics = []
        now = datetime.now()
        for r in range(1, self.history_count + 1):
            then = now - relativedelta(months=r)
            periodics.append((then.month, then.year))

        return periodics

    def get_product_supplier_info(self, product_id):
        """Get supplier info for the product.
        :param product_id: product
        :return: res.partner supplier Id, or False if not match
        """
        print('get_product_supplier_info')
        product = self.env["product.product"].search([("id", "=", product_id)])
        if self.supplier:
            info_domain = [("product_tmpl_id", "=", product.product_tmpl_id.id), ("partner_id.name", "=", self.supplier.id)]
        else:
            info_domain = [("product_tmpl_id", "=", product.product_tmpl_id.id)]

        supplier = self.env["product.supplierinfo"].search(info_domain, order="sequence", limit=1)
        return supplier.id if supplier else False

    def mtd_sql(self, usage):
        # TODO need to handle returns
        dt_obj = fields.Datetime.now()
        midnight_datetime = datetime(day=1, month=dt_obj.month, year=dt_obj.year, hour=0, minute=0, second=0)
        move_start_date = pytz.UTC.localize(midnight_datetime)

        sql_string = """
                select sum(product_uom_qty) from stock_move, stock_location 
                where state != 'cancel' and stock_move.company_id = {company} 
                and date between '{start_date}' and '{end_date}' 
                and location_dest_id = stock_location.id 
                and usage = '{usage}'
            """

        self.env.cr.execute(
            sql_string.format(
                company=self.env.company.id, start_date=move_start_date, end_date=datetime.now(), usage=usage
            )
        )
        rec = self.env.cr.fetchall()
        return rec[0][0]

    def get_mtd_demand(self, product, ptype):
        if ptype == "sale":
            this_mtd_qty = self.mtd_sql(usage="sale")
        else:
            this_mtd_qty = self.mtd_sql(usage="production")
        if isinstance(this_mtd_qty, int):
            return this_mtd_qty
        else:
            return 0

    def build_forecast(self, product_periods):
        """
        Use SARIMAX to guess forecast values from line.actual quantities.

        :param product_periods: dictionary of {product_id, ProductPeriod}
        """

        def _periodic_ref():
            """
            List of years and months for forecast plots
            """
            periodics = []
            now = datetime.now()
            if self.forecast_from == "this_month":
                month_count = self.forecast_count
            else:
                month_count = self.forecast_count + 1
            for r in range(0, month_count):
                if r:
                    then = now + relativedelta(months=r)
                else:
                    then = now
                if not r and self.forecast_from == "next_month":
                    continue
                else:
                    periodics.append((then.month, then.year))
            return periodics

        plot_model = self.env["forecast.data.plot"]

        p = d = q = range(0, 2)
        pdq = list(itertools.product(p, d, q))
        seasonal_pdq = [(x[0], x[1], x[2], 12) for x in list(itertools.product(p, d, q))]
        reference = _periodic_ref()

        if self.plot_type:
            plot_types = ["sale", "mfg"]
        else:
            plot_types = ["sale"]

        for product_id, product_period in product_periods.items():
            for ptype in plot_types:

                plots = []
                for plot in product_period.line.product_plots:
                    if plot.type == ptype:
                        plots.append(plot)
                plots = sorted(plots, key=lambda p: p.year * 100 + p.month)

                data = [p.actual for p in plots]
                min_aic = sys.maxsize
                best_fit = None

                try:
                    model = pmd.auto_arima(data,start_p=1, start_q=1, test='adf', m=12, seasonal=True, trace=True)
                except:
                    next
                sarima = SARIMAX(data, order=(1, 1, 1), seasonal_order=(1, 0, 1, 12))
                predicted = sarima.fit().predict();predicted
                plt.figure(figsize=(20, 6))
                plt.plot(data, label='Actual')
                plt.plot(predicted, label='Predicted')
                plt.legend()

                _log.debug(f"Forecasted product: {product_period.line.product}, ptype: {ptype}")

                # Update forecast values in history
                data_len = len(data)
                #forecast = predicted.predict(0, data_len + self.forecast_count)
                for i in range(0, data_len):
                    plots[i].write({"forecast": predicted[i]})
                # Create future forecast values
                for i, period in enumerate(reference):
                    month, year = period
                    rounded_forecast = math.ceil(predicted[i])
                    if i == 0 and self.forecast_from == "this_month":
                        # need to offset any units sold MTD
                        mtd_qty = self.get_mtd_demand(product_period.line.product, ptype)
                        rounded_forecast -= mtd_qty
                    if rounded_forecast < 0:
                        rounded_forecast = 0
                    plot_model.create(
                        {
                            "forecast_line": product_period.line.id,
                            "type": ptype,
                            "year": year,
                            "month": month,
                            "forecast": rounded_forecast,
                            "actual": 0,
                            "forecasted": True,
                            "actual_forecast": rounded_forecast,
                        }
                    )

    def button_generate_forecast(self):
        # self.with_delay(channel=self.heavy_job_channel(), description="Forecast Data {}".format(self.name))._button_generate_forecast()
        self._button_generate_forecast()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'target': 'new',
            'params': {
                'message': _("Task Added Forecast Data [{}] to Job Queue").format(self.name),
                'type': 'info',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }



class ForecastDataLine(models.Model):
    _name = "forecast.data.line"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    ################################################################################
    # Fields
    ################################################################################

    forecast_data = fields.Many2one("forecast.data", string="Forecast Data", required=True, ondelete="cascade")
    product = fields.Many2one("product.product", string="Product", readonly=True)
    template = fields.Many2one("product.template", related="product.product_tmpl_id", readonly=True)
    supplierinfo = fields.Many2one("product.supplierinfo", string="Supplier")
    available = fields.Float(string="Available", required=True, default=0, readonly=True)
    on_order = fields.Float(string="On Order", required=True, default=0, readonly=True)
    draft_sale = fields.Float(string="Sale Quotations", required=True, default=0, readonly=True)
    draft_mo = fields.Float(string="Draft MO", required=True, default=0, readonly=True)
    forecast = fields.Float(string="Forecast", required=True, default=0)
    cover = fields.Float(string="SOH Cover")
    suggested_qty = fields.Float(string="Suggested", required=True, default=0)
    order_qty = fields.Float(string="Now Order Qty", default=0)
    currency = fields.Many2one(comodel_name="res.currency", string="Currency")
    buy_price = fields.Float(string="Buy Price")
    state_flag = fields.Selection(
        selection=[("1", "No issue"), ("2", "ReOrder"), ("3", "Reorder Issue"), ("4", "Indent Product")],
        default="1",
        string="Stock State",
        help="1: No Issue \n2: ReOrder required but no runout, \n3: Reorder Required and expected stock shortage 4\n: Indent Product",
    )
    method = fields.Selection(
        string="Method",
        selection=[
            ("linear", "Linear"),
            ("periodic", "Periodic"),
        ],
        required=True,
    )
    note = fields.Text(string="Notes")

    purchase = fields.Many2one("purchase.order", readonly=True)
    manufacturing = fields.Many2one("mrp.production", readonly=True)
    product_plots = fields.One2many("forecast.data.plot", "forecast_line")
    delay = fields.Integer(string="Supplier Lead Time")
    required_cover = fields.Integer(string="Planned Cover Days")

    _sql_constraints = [
        (
            "unique_forecast_data_product",
            "unique(forecast_data, product)",
            "Product forecast lines must be unique for a forecast",
        )
    ]

    ###########################################################################
    # Model methods
    ###########################################################################

    def update_quantities(self, locations):
        """
        Update/Compute the quantity values from various sources.
        - avail - do not use free_qty ad Deeco backorder logic unreserves the stock so free_qty not correct
        - on_order
        - suggested_qty: determine from forecast.data.plot
        """

        available = (
            self.product.with_context(location=locations.ids).qty_available
            - self.product.with_context(location=locations.ids).outgoing_qty
        )
        on_order = self.product.with_context(location=locations.ids).incoming_qty

        draft_sale_lines = self.env["sale.order.line"].search(
            [("product_id", "=", self.product.id), ("state", "=", "draft")]
        )
        draft_sale = sum([x.product_uom_qty for x in draft_sale_lines])
        draft_production = self.env["mrp.production"].search(
            [("product_id", "=", self.product.id), ("state", "=", "draft")]
        )
        draft_mo = sum([x.product_qty for x in draft_production])

        forecast_total = sum([p.forecast for p in self.product_plots.filtered("forecasted")])
        soh_cover = self.calculate_soh_cover(available, on_order, forecast_total)
        delay = self.calculated_supplier_lead_time()
        required_cover_days = (
            self.supplierinfo.purchase_demand_cover
            or self.product.categ_id.purchase_demand_cover
            or self.forecast_data.company.purchase_demand_cover
        )
        suggestion, state_flag, order_qty = self.compute_suggested(
            available, on_order, forecast_total, delay, required_cover_days
        )
        self.write(
            {
                "available": available,
                "on_order": on_order,
                "draft_sale": draft_sale,
                "draft_mo": draft_mo,
                "forecast": forecast_total,
                "cover": soh_cover,
                "suggested_qty": suggestion,
                "order_qty": order_qty,
                "currency": self.supplierinfo.currency_id.id,
                "state_flag": state_flag,
                "buy_price": self.supplierinfo.price,
                "delay": delay,
                "required_cover": required_cover_days,
            }
        )

    def calculate_soh_cover(self, available, on_order, forecast_total):
        monthly_forecast = forecast_total / self.forecast_data.forecast_count
        if monthly_forecast:
            cover = (available + on_order) / monthly_forecast
        else:
            if self.product.indent_product:
                cover = 0
            else:
                cover = 999

        return cover

    def calculated_supplier_lead_time(self):
        if self.supplierinfo.delay:
            delay = self.supplierinfo.delay
        elif self.supplierinfo.partner_id.delay:
            delay = self.supplierinfo.partner_id.delay
        else:
            delay = 0.0

        return delay

    def compute_suggested(self, available, on_order, forecast_total, delay, cover_days):
        """
        Intepret:
            forecasted demand
            supplier delivery time
            available quantities
            on order quantities
            configured cover-days

        and magically come up with a suggested quantity.

        :param available: available stock
        :param on_order: on order/on its way
        :return:
        """
        plots = self.product_plots.filtered("forecasted")
        state_flag = "1"

        # Daily demand is pro-rated per month over the FORECAST_COUNT months, using 30-day months
        daily_demand = forecast_total / self.forecast_data.forecast_count / 30
        if daily_demand < 0 or not delay:
            if self.product.indent_product:
                state_flag = "4"
            elif available < 0:
                state_flag = "3"
            return 0, state_flag, 0

        if cover_days and cover_days < 31:
            min_stock = plots[0].forecast * (cover_days / 30)
        elif cover_days and cover_days < 62 and len(plots) > 1:
            min_stock = plots[0].forecast + (plots[1].forecast * ((cover_days - 30) / 30))
        else:
            min_stock = cover_days * daily_demand

        if delay and delay < 31:
            consumed_stock = plots[0].forecast * (delay / 30)
        elif delay and delay < 62 and len(plots) > 1:
            consumed_stock = plots[0].forecast + (plots[1].forecast * ((delay - 30) / 30))
        else:
            consumed_stock = delay * daily_demand

        # At any point in time, we have no idea whether ordered-quantities will
        # arrive before we run out; but the assumption is that it will.
        #
        # It doesn't matter if the delivery time takes longer than the re-order period,
        # as suggested quantity already takes into account the in-flight order quantities.
        #
        # Thus the suggested quantity is as simple as the difference between
        # the minumum stock the expected quantity after the delivery lead time
        #
        suggestion = min_stock - (available + on_order - consumed_stock)
        if self.product.indent_product:
            order_qty = 0.0
        else:
            order_qty = suggestion

        if suggestion < 0:
            if self.product.indent_product:
                state_flag = "4"
            return 0, state_flag, 0

        # need to round to whole number and order minimum for the supplier
        if self.supplierinfo.min_qty and suggestion < self.supplierinfo.min_qty:
            order_qty = self.supplierinfo.min_qty
            state_flag = "2"
        if available + on_order - consumed_stock < 0:
            state_flag = "3"
        if self.product.indent_product:
            state_flag = "4"
        suggestion = math.ceil(suggestion)
        order_qty = math.ceil(order_qty)

        return suggestion, state_flag, order_qty

    def get_graph_view(self):

        return self.env.ref("purchase_demand_planning.action_forecast_data_line")

    def button_graph_demand(self):
        """
        Generate graph view using forecast.data.plot associated with this line.
        :return:
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Product Demand ({})".format(self.product.name),
            "view_mode": "pivot,graph,list",
            "act_window_id": self.get_graph_view().id,
            "res_model": "forecast.data.plot",
            "domain": [
                ("forecast_line", "=", self.id),
                ("type", "=", "sale"),
            ],
            "target": "current",
        }


class ForecastDataPlot(models.Model):
    _name = "forecast.data.plot"

    ###########################################################################
    # Default and compute methods.
    ###########################################################################

    @api.depends('year', 'month')
    def _build_date(self):
        for p in self:
            if p.year and p.month and p.year > 0 and 1 <= p.month <= 12:
                p.date = "%04d-%02d-01" % (p.year, p.month)
            else:
                p.date = False

    @api.depends("month", "forecasted")
    def _month_and_act_or_fcast(self):
        for rec in self:
            if rec.forecasted:
                if rec.month < 10:
                    rec.month_and_type = "0" + str(rec.month) + "F"
                else:
                    rec.month_and_type = str(rec.month) + "F"
            else:
                if rec.month < 10:
                    rec.month_and_type = "0" + str(rec.month) + "A"
                else:
                    rec.month_and_type = str(rec.month) + "A"

    ################################################################################
    # Fields
    ################################################################################

    forecast_line = fields.Many2one("forecast.data.line", required=True, ondelete="cascade")
    product = fields.Many2one(comodel_name="product.product", related="forecast_line.product", string="Product")
    type = fields.Selection(string="Type", selection=[("sale", "Sale"), ("mfg", "Manufacturing")], required=True)
    date = fields.Date("Month Start", compute="_build_date", store=True, readonly=True)
    month = fields.Integer("Month", required=True, default=0)
    month_and_type = fields.Char(string="Month", compute="_month_and_act_or_fcast", store=True, readonly=True)
    year = fields.Integer("Year", required=True, default=0)
    actual = fields.Float(string="Historical", required=True, default=0)
    forecast = fields.Float(string="Forecast", required=True, default=0)
    forecasted = fields.Boolean(string="Qty values are forecasted")
    actual_forecast = fields.Float(string="Quantity")

    ###########################################################################
    # Model methods
    ###########################################################################
