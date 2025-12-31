import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { ControlPanel } from "@web/search/control_panel/control_panel";
import { formatMonetary } from "@web/views/fields/formatters";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

import { Component, onWillStart, useChildSubEnv, useState } from "@odoo/owl";

import { StockReconciliationReportController } from "@account_immediate/stock_reconciliation/controller"
import { StockValuationReportFilters } from "@stock_account/stock_valuation/filters/filters"

const { DateTime } = luxon;


export class StockReconciliationReport extends Component {
    static template = "account_immediate.StockReconciliationReport";
    static props = { ...standardActionServiceProps };
    static components = {
        ControlPanel,
        StockValuationReportFilters,
    };

    setup() {
        this.controller = useState(new StockReconciliationReportController(this.props.action));
        this.state = useState({
            displayInventoryValuationLine: false,
        })
        this.orm = useService("orm");
        this.actionService = useService("action");
        this._t = _t;

        onWillStart(async () => {
            await this.controller.load(this.data);
        })

        useChildSubEnv({
            _t,
            controller: this.controller,
            formatMonetary: this.formatMonetary.bind(this),
        });
    }

    formatMonetary(value) {
        return formatMonetary(value, {
            currencyId: this.data.currency_id,
        });
    }

    // Getters -----------------------------------------------------------------
    get data() {
        return this.controller.data || {};
    }

    onClickExplainDispatchedNotInvoiced () {
        const domain = [
            ["reconciliation_id", "=", this.data.res_id],
        ];
        return this.actionService.doAction({
            name: 'Dispatched Not Invoiced',
            type: "ir.actions.act_window",
            res_model: "account.stock.reconcile.dni",
            views: [[false, 'list']],
            domain: domain,
            target: 'current',
        });
    }


    onClickExplainReceivedNotInvoiced () {
        const domain = [
            ["reconciliation_id", "=", this.data.res_id],
        ];
        return this.actionService.doAction({
            name: 'Received Not Invoiced',
            type: "ir.actions.act_window",
            res_model: "account.stock.reconcile.rni",
            views: [[false, 'list']],
            domain: domain,
            target: 'current',
        });
    }


    onClickExplainUnexplained () {
        const domain = [
            ["reconciliation_id", "=", this.data.res_id],
        ];
        return this.actionService.doAction({
            name: 'Other',
            type: "ir.actions.act_window",
            res_model: "account.stock.reconcile.other",
            views: [[false, 'list']],
            domain: domain,
            target: 'current',
        });
    }

}

registry.category("actions").add("stock_reconciliation_report", StockReconciliationReport);
