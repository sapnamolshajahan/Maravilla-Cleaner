import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { ControlButtons } from "@point_of_sale/app/screens/product_screen/control_buttons/control_buttons";
import { patch } from "@web/core/utils/patch";
import { LoyaltyPopupWidget } from "@sale_pos_ecomm_loyalty/js/LoyaltyPopupWidget";

patch(ControlButtons.prototype, {
    async clickRedeem() {
        let order = this.env.services.pos.get_order();
        let self = this;
        let partner = false;
        let loyalty_points = 0;
        if (order.lines.length > 0) {
            if (this.pos.pos_loyalty_setting.length != 0) {
                if (order.get_partner() != null) {
                    partner = order.get_partner();
                    loyalty_points = partner.loyalty_pts;
                }
                if (order.redeem_done) {
                    this.pos.dialog.add(AlertDialog, {
                        title: _t('Redeem Product'),
                        body: _t('Sorry, you already added the redeem product.'),
                    });
                } else if (this.pos.pos_loyalty_setting[0].redeem_ids.length == 0) {
                    this.pos.dialog.add(AlertDialog, {
                        title: _t('No Redemption Rule'),
                        body: _t('Please add Redemption Rule in loyalty configuration'),
                    });
                } else if (!partner) {
                    this.pos.dialog.add(AlertDialog, {
                        title: _t('Unknown customer'),
                        body: _t('You cannot redeem loyalty points. Select customer first.'),
                    });
                } else if (loyalty_points < 1) {
                    this.pos.dialog.add(AlertDialog, {
                        title: _t('Insufficient Points'),
                        body: _t('Sorry, you do not have sufficient loyalty points.'),
                    });
                } else {
                    this.pos.dialog.add(LoyaltyPopupWidget, {'partner': partner});
                }
            }
        } else {
            this.pos.dialog.add(AlertDialog, {
                title: _t('Empty Order'),
                body: _t('Please select some products'),
            });
        }
    }
});


