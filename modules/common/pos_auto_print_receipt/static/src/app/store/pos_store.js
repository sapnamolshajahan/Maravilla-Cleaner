import { PosStore } from "@point_of_sale/app/services/pos_store";
import {patch} from "@web/core/utils/patch";

patch(
    PosStore.prototype,
    {
        /**
         * Override to let backend handle printing.
         */
        async printReceipt(
            {
                basic = false,
                order = this.get_order(),
                printBillActionTriggered = false,
            } = {})
       {
            this.data.call(
                "pos.order",
                "print_pos_auto",
                [order.id]
            );
            return true;
       }
    });
