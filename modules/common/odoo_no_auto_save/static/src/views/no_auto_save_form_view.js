/** @odoo-module **/

import { FormController } from "@web/views/form/form_controller";
import { AccountMoveFormRenderer } from '@account/components/account_move_form/account_move_form';
import { patch } from "@web/core/utils/patch";

patch(FormController.prototype, {
    //This is needed to avoid the auto save when unload
    beforeUnload(ev) {},

    //This is needed to avoid the auto save when visibility change
    beforeVisibilityChange() {}
});

patch(AccountMoveFormRenderer.prototype, {
    async saveBeforeTabChange() {
        if (this.props.record.isInEdition && await this.props.record.isDirty()) {
            const contentEl = document.querySelector('.o_content');
            const scrollPos = contentEl.scrollTop;
            if (scrollPos) {
                contentEl.scrollTop = scrollPos;
            }
        }
    }
});
