/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { knowledgeHtmlField } from "@knowledge/components/knowledge_html_field/knowledge_html_field";

patch(knowledgeHtmlField, {
    extractProps({ attrs, options }, dynamicInfo) {
        const props = super.extractProps({ attrs, options }, dynamicInfo);
        return {
            ...props,
            codeview: Boolean(odoo.debug && options.codeview !== false),
        };
    },
});
