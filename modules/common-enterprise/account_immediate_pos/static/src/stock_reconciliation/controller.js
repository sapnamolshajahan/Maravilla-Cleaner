import { reactive } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
const { DateTime } = luxon;


export class StockReconciliationReportController {
    constructor(action) {
        this.action = action;
        this.actionService = useService("action");
        this.dialog = useService("dialog");
        this.orm = useService("orm");
        this.state = reactive({
            date: DateTime.now(),
        });
    }

    async load() {
        await this.loadReportData();
        this.currencyId = this.data.currency_id;
        this.companyId = this.data.company_id;
    }

    async loadReportData() {
        const kwargs = {
            date: this.state.date.toFormat("yyyy-MM-dd"),
        };
        const res = await this.orm.call(
            "account_immediate.stock.reconciliation.report",
            "get_report_values",
            [],
            kwargs
        );
        this.data = res.data;
    }

    async setDate(date) {
        this.state.date = date;
        this.dateAsString = date.toFormat('y-LL-dd HH:mm:ss');
        await this.loadReportData();
    }

    actionPrintReport(format="pdf") {
        if (format === "pdf") {
            return this.orm.call("account_immediate.stock.reconciliation.report", "action_print_as_pdf");
        } else if (format === "xlsx") {
            return this.orm.call("account_immediate.stock.reconciliation.report", "action_print_as_xlsx");
        }
    }
}
