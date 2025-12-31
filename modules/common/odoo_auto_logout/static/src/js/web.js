/** @odoo-module */

import { browser } from "@web/core/browser/browser";
import { session } from "@web/session";
import { registry } from "@web/core/registry";


export const myService = {
    dependencies: ["orm"],
    async start(env, { rpc }) {
        const result = await env.services.orm.call(
            'res.company',
            'read',
            [[1],['logout_time']],
        );
        if(result){
            window.timeout = setTimeout(function() {
                    window.location.href = "/web/session/logout?redirect=/";
                }, result[0]['logout_time'] *1000);
            browser.addEventListener("mousemove", () => {
                if (window.timeout !== null) {
                    clearTimeout(window.timeout);
                }
                window.timeout = setTimeout(function() {
                    window.location.href = "/web/session/logout?redirect=/";
                }, result[0]['logout_time'] *1000);
            });
        }
    },
};

registry.category("services").add("myuser", myService);

