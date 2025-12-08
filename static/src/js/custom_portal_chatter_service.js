/** @odoo-module **/

import { App } from "@odoo/owl";
import { AssetsLoadingError, getBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";
import { session } from "@web/session";
import { _t } from "@web/core/l10n/translation";
import { getTemplate } from "@web/core/templates";
import { PortalChatter } from "@portal/chatter/frontend/portal_chatter";

export class CustomPortalChatterService {
    constructor(env, services) {
        this.setup(env, services);
    }

    setup(env, services) {
        this.store = services["mail.store"];
        this.busService = services.bus_service;
    }

    async createShadow(root) {
        const shadow = root.attachShadow({ mode: "open" });
        try {
            const res = await getBundle("portal.assets_chatter_style");
            for (const url of res.cssLibs) {
                const link = document.createElement("link");
                link.rel = "stylesheet";
                link.href = url;
                shadow.appendChild(link);
                await new Promise((res, rej) => {
                    link.addEventListener("load", res);
                    link.addEventListener("error", rej);
                });
            }
        } catch (e) {
            if (e instanceof AssetsLoadingError && e.cause instanceof TypeError) {
                return new Promise(() => {});
            } else {
                throw e;
            }
        }
        return shadow;
    }

    async initialize(env) {
        const chatterElements = document.querySelectorAll(".o_portal_chatter");
        if (!chatterElements.length) return;

        for (const chatterEl of chatterElements) {
            const props = {
                resId: parseInt(chatterEl.getAttribute("data-res_id")),
                resModel: chatterEl.getAttribute("data-res_model"),
                composer:
                    parseInt(chatterEl.getAttribute("data-allow_composer")) &&
                    (chatterEl.getAttribute("data-token") || !session.is_public),
                twoColumns: chatterEl.getAttribute("data-two_columns") === "true",
                displayRating: chatterEl.getAttribute("data-display_rating") === "True",
            };

            const root = document.createElement("div");
            root.classList.add("chatterRoot");
            if (props.twoColumns) root.classList.add("p-0");
            chatterEl.appendChild(root);

            const shadow = await this.createShadow(root);

            new App(PortalChatter, {
                env,
                getTemplate,
                props,
                translatableAttributes: ["data-tooltip"],
                translateFn: _t,
                dev: env.debug,
            }).mount(shadow);

            // Insert thread into store
            const thread = this.store.Thread.insert({ model: props.resModel, id: props.resId });
            Object.assign(thread, {
                access_token: chatterEl.getAttribute("data-token"),
                hash: chatterEl.getAttribute("data-hash"),
                pid: parseInt(chatterEl.getAttribute("data-pid")),
            });

            const data = await rpc(
                "/portal/chatter_init",
                {
                    thread_model: props.resModel,
                    thread_id: props.resId,
                    ...thread.rpcParams,
                },
                { silent: true }
            );

            this.store.insert(data);
        }

        odoo.portalChatterReady.resolve(true);
    }
}

// Fully override the service in the registry
export const customPortalChatterService = {
    dependencies: ["mail.store", "bus_service"],
    start(env, services) {
        const portalChatter = new CustomPortalChatterService(env, services);
        portalChatter.initialize(env);
        return portalChatter;
    },
};

registry.category("services").add("portal.chatter", customPortalChatterService, { force: true });
