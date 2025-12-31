/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { htmlField as HtmlEditorField } from "@html_editor/fields/html_field";

// Patch the html_editor's htmlField
patch(HtmlEditorField, {
    extractProps({ attrs, options }, dynamicInfo) {
        const props = super.extractProps({ attrs, options }, dynamicInfo);
        return {
            ...props,
            codeview: options.codeview !== false,
        };
    },
});
