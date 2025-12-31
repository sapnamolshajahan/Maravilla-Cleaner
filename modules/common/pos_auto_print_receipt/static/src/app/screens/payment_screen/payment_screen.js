import {PaymentScreen} from "@point_of_sale/app/screens/payment_screen/payment_screen";
import {patch} from "@web/core/utils/patch";

patch(
    PaymentScreen.prototype,
    {
        /**
         * Override to disable auto invoice-download.
         */
        shouldDownloadInvoice()
        {
            return false;
        },

        /**
         * Override: Use backend-printing mechanism to open cashbox.
         */
        openCashbox()
        {
            this.pos.data.call("pos.config", "open_cashbox", [this.pos.config.id])
        }
    });
