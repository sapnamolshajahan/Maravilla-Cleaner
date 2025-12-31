/** @odoo-module **/
/** payment smartpay */

import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/payment/payment_interface";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { rpc } from "@web/core/network/rpc";



export class PaymentSmartPay extends PaymentInterface {

    /*
     * Override external interfaces.
     */
    send_payment_request (cid){
            super.send_payment_request(cid);
            this._reset_state();
            return this._smartpay_pay();
        }

    send_payment_cancel (order, cid){
            super.send_payment_cancel(...arguments);
            // set only if we are polling
            this.was_cancelled = !!this.polling;
            this._smartpay_cancel();
            return new Promise(function (resolve, reject){
                    resolve(true);
                    return Promise.resolve();
                });
        }

    /*
     * Internal Methods
     */
    _reset_state (){
        this.was_cancelled = false;
        this.last_diagnosis_service_id = false;
        this.remaining_polls = 15;
        clearTimeout(this.polling);
    }

    _handle_odoo_connection_failure (data){
        // handle timeout
        var line = this.pos.get_order()?.get_selected_paymentline();
        if (line)
            line.set_payment_status('retry');
        this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'));

        return Promise.reject(data); // prevent subsequent onFullFilled's from being called
    }

    async _call_smartpay (data, operation){
        const notification = await this.pos.data.silentCall(
            "pos.payment.method",
            "proxy_smartpay_request",
            [[this.payment_method_id.id], data, operation]
        );

        if (!notification) {
            this._handle_odoo_connection_failure();
            return;
        }

        return notification;
    }

    _smartpay_pay (){
            var self = this;
            var config = this.pos.config;
            var order = this.pos.get_order();
            var line = order.get_selected_paymentline();
            console.log(line.uuid);
            var data = {
                "pos": config.id,
                "order": order.id,
                "transaction": line.uuid,
                "amount": line.amount,
            };

            return this
                ._call_smartpay(data)
                .then(
                    function (data)
                    {
                        return self._smartpay_pay_response(data);
                    });
        }

    _smartpay_cancel (){
            /*
             * This is just stub code, as Smartpay doesn't have API support
             * for the POS to abort the transaction.
             */
        }

    async _poll_pay_response (resolve, reject, txid){
            var self = this;
            if (this.was_cancelled) {
                resolve(false);
                return Promise.resolve();
            }

            const response = await this.pos.data.silentCall(
                "pos.payment.method",
                "get_smartpay_status",
                [[this.payment_method_id.id], txid]
            );

            if (!response) {
                Promise.reject();
                return this._handle_odoo_connection_failure();
            }

            self.remaining_polls--;

            var order = self.pos.get_order();
            var state = response.state;

            if (state == "success")
            {
                resolve(true);

            } else if (state == "error")
            {
                self._show_error(_t("Message from Smartpay: %s"), response.message);
                this.pos.get_order().get_selected_paymentline().set_payment_status("retry");
                resolve(false);

            } else if (self.remaining_polls <= 0)
            {
                self._show_error(_t('The connection to your payment terminal failed. Please check if it is still connected to the internet.'));
                self._smartpay_cancel();
                resolve(false);
            }
    }

    _smartpay_pay_response (response){
            var order = this.pos.get_order();
            var line = this.pos.get_order()?.get_selected_paymentline();

            if (!response.submit)
            {
                this._show_error(_t(response.error));
                if (line)
                    line.set_payment_status('force_done');
                return Promise.resolve();
            }

            line.transaction_id = response.transaction;     // record for cancel/re-try
            line.set_payment_status('waitingCard');         // this saves to local-store

            var self = this;
            var res = new Promise( function (resolve, reject)
                {
                    // clear previous intervals just in case, otherwise it'll run forever
                    clearTimeout(self.polling);

                    self.polling = setInterval(
                        function ()
                        {
                            self._poll_pay_response(resolve, reject, response.transaction);
                        }, 4000);
                });

            // make sure to stop polling when we're done
            res.finally (
                function ()
                {
                    self._reset_state();
                });

            return res;
        }


    _show_error (msg, title){
            if (!title) {
                this.env.services.dialog.add(AlertDialog, {
                    title: _t("Smartpay Error"),
                    body: msg,
                });
            }
    }
}



