/** @odoo-module **/

import { PortalHomeCounters } from '@portal/js/portal';

PortalHomeCounters.include({
    /**
     * @override
     */
    _getCountersAlwaysDisplayed() {
        return this._super(...arguments).filter(
            (counter) => counter !== 'invoice_count' && counter !== 'order_count'
        );
    },
});