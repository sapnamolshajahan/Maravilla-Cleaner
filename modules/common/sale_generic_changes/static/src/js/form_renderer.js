/** @odoo-module **/

import { FormRenderer } from "@web/views/form/form_renderer";
import { patch } from "@web/core/utils/patch";
import { onMounted } from "@odoo/owl";

patch(FormRenderer.prototype, {
    setup() {
        super.setup();
        onMounted(() => {
            const activeElement = this.uiService.activeElement;
            if (activeElement && this.props.record.resModel === 'sale.order'){
                const element = activeElement.querySelector(".o_form_renderer");
                const element2 = activeElement.querySelector(".o_form_sheet_bg");
                if (element){
                    element.classList.remove("d-flex");
                }
                if (element2) {
                    element2.style.setProperty("max-width", "none", "important");
                }
            }
        });
    }
});
