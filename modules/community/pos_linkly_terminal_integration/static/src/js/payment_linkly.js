/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { _t } from "@web/core/l10n/translation";
import { PaymentInterface } from "@point_of_sale/app/utils/payment/payment_interface";
import { sprintf } from "@web/core/utils/strings";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";

export class LINKLY extends PaymentInterface {
    setup(){
        super.setup(...arguments);
    }
    sendPaymentRequest (uuid) {
        super.sendPaymentRequest(uuid);
        this._reset_state();
        var order = this.pos.getOrder();
        var line = order.getSelectedPaymentline();
        if (line && (line.amount < 0) && !order.txnRef) {
            this._show_error(_t("Cannot procced with the refund transaction, as this order doesn't have the transaction reference of the original order. Please contact your administrator."));
        } else {
            return this._linklyPay(uuid);
        }
    }
    sendPaymentCancel (order, uuid) {
        super.sendPaymentCancel(order, uuid);
        return this._linkly_cancel();
    }
    close() {
        this.close();
    }
    pending_linkly_line() {
        return this.pos.getOrder().payment_ids.find(
            paymentLine => paymentLine.payment_method_id.use_payment_terminal === 'linkly' && (!paymentLine.is_done()));
    }
    _reset_state () {
        this.was_cancelled = false;
        this.remaining_polls = 4;
        clearTimeout(this.polling);
    }
    _handleOdooConnectionFailure (data) {
        var line = this.pending_linkly_line();
        if (line && line.set_payment_status) {
            line.set_payment_status('retry');
            line.fail_transaction = true
        }
        this._show_error(_t('Could not connect to the Odoo server, please check your internet connection and try again.'));

        return Promise.reject(data); // prevent subsequent onFullFilled's from being called
    }
    _call_linkly(data, operation = false) {
        data.pos_session_id = data.pos_session_id.id
        return this.pos.data
            .silentCall("pos.payment.method", "proxy_linkly_request", [
                data
            ]).catch(this._handleOdooConnectionFailure.bind(this));
    }
    _linkly_get_sale_id () {
        return sprintf("%s (ID: %s)", config.display_name, this.pos.config.id);
    }
    _linkly_pay_data () {
        var order = this.pos.getOrder();
        var line = order.getSelectedPaymentline();
        var data = {
            "order_ref":order.name,
            "amount":line.amount >= 0 ? line.amount : -1*line.amount,
            'txnType': line.amount >= 0 ? "P" : 'R',
            'payment_method_id':parseInt(line.payment_method_id.id),
            'pos_session_id':order.session_id,
            'RFN':order.txnRef,
            'UID':order.uuid,
            'OPR':this.pos.user.id + ' | ' + this.pos.user.name,
        }
        return data;
    }
    generate_UUID() {
        return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function (c) {
            const r = Math.random() * 16 | 0, v = c == 'x' ? r : (r & 0x3 | 0x8);
            return v.toString(16);
        });
    }
    _linklyPay (cid) {
        var self = this;
        var order = this.pos.getOrder();
        if (order === this.poll_error_order) {
            delete this.poll_error_order;
            return self._linkly_handle_response({});
        }

        var data = this._linkly_pay_data();
        var line = order.payment_ids.find(paymentLine => paymentLine.uuid === cid);
        line.setTerminalServiceId(this.most_recent_service_id);
        if(line.fail_transaction){
            data.linkly_payment_UUID = line.linkly_payment_UUID
            data.fail_transaction = true
        } else {
            line.linkly_payment_UUID = self.generate_UUID()
            data.linkly_payment_UUID = line.linkly_payment_UUID
        }
        return this._call_linkly(data).then(function (data) {
            console.log("data : ",data)
            return self._linkly_handle_response(data);
        }).catch(function(err){
            console.log("errr ------->",err)
        })
    }
    async _linkly_cancel (ignore_error) {
        var self = this;
        self._show_error(_t('Cancelling the payment failed. Please cancel it manually on the payment terminal.'));
        self.was_cancelled = !!self.polling;
        // return Promise.reject();
        return Promise.resolve();
    }
    _poll_for_response (resolve, reject) {
        if (this.was_cancelled) {
            resolve(false);
            return Promise.resolve();
        }
    }
    _linkly_handle_response (response) {
        var self = this;
        console.log("response : ",response)
        if(response){
            if(response.responseType == "transaction"){
                var response = response.response
                if (response.responseCode == '00' && response.responseText.includes('APPROVED')){
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    line.txnRef = response.txnRef
                    line.cardType = response.cardName;
                    line.cardholder_name = response.cardName
                    if(line && line.set_payment_status){
                        var wk_date = new Date(response.date); 
                        var accountType = 'SAVINGS ACCOUNT'
                        if(response.accountType == '2')
                            accountType = 'CHEQUE ACCOUNT'
                        else if (response.accountType == '3')
                            accountType = 'CREDIT ACCOUNT'
                        var txnType = 'PURCHASE     ' + self.pos.currency.name + ''
                        if(response.txnType == 'R')
                            txnType = '** REFUND **'
                        var amtPurchase = response.amtPurchase
                        if (line && line.payment_method && line.payment_method.linkly_test_mode)
                            amtPurchase = response.amtPurchase/100

                        var receipt_data = `
                        ---------------------------------
                                        `+self.pos.config.name+`

                        `+wk_date.toLocaleString().split(',')[1]+` `+ wk_date.toLocaleString().split(',')[0] +` 

                        `+accountType+`

                        `+txnType+`          `+self.pos.currency.symbol+``+amtPurchase+`

                                                ---------

                        TOTAL        `+self.pos.currency.name+`          `+self.pos.currency.symbol+``+amtPurchase+`

                        APPROVED  -  00
                        
                        PLEASE RETAIN AS RECORD OF PURCHASE
                        ---------------------------------
                        `
                        line.linkly_receipt = receipt_data
                        line.set_payment_status('done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve(true);
                }if (response.responseCode == '08' && response.responseText.includes('APPROVED')){
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    line.txnRef = response.txnRef
                    line.cardType = response.cardName;
                    line.cardholder_name = response.cardName
                    if(line && line.set_payment_status){
                        var wk_date = new Date(response.date); 
                        var accountType = 'SAVINGS ACCOUNT'
                        if(response.accountType == '2')
                            accountType = 'CHEQUE ACCOUNT'
                        else if (response.accountType == '3')
                            accountType = 'CREDIT ACCOUNT'
                        var txnType = 'PURCHASE     ' + self.pos.currency.name + ''
                        if(response.txnType == 'R')
                            txnType = '** REFUND **'
                        var amtPurchase = response.amtPurchase
                        if (line && line.payment_method && line.payment_method.linkly_test_mode)
                            amtPurchase = response.amtPurchase/100

                        var receipt_data = `
                        ---------------------------------
                                        `+self.pos.config.name+`

                        `+wk_date.toLocaleString().split(',')[1]+` `+ wk_date.toLocaleString().split(',')[0] +` 

                        `+accountType+`

                        `+txnType+`          `+self.pos.currency.symbol+``+amtPurchase+`

                                                ---------

                        TOTAL        `+self.pos.currency.name+`          `+self.pos.currency.symbol+``+amtPurchase+`

                        APPROVED  -  00
                        
                        PLEASE RETAIN AS RECORD OF PURCHASE
                        ---------------------------------
                        `
                        line.linkly_receipt = receipt_data
                        line.set_payment_status('done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve(true);
                } else if (response.responseCode == 'TM' && response.responseText.includes('OPERATOR CANCELLED')){
                    // Promise.reject();
                    // self.poll_error_order = self.pos.getOrder();
                    // return self._handleOdooConnectionFailure(response);
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    self._show_error(_t('Transaction cancelled on the payment terminal. Please retry or select a different payment option.'));
                    if(line && line.set_payment_status){
                        line.set_payment_status('force_done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve();
                } else if (response.responseCode == 'TI' && response.responseText.includes('OPERATOR TIMEOUT')){
                    // Promise.reject();
                    // self.poll_error_order = self.pos.getOrder();
                    // return self._handleOdooConnectionFailure(response);
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    self._show_error(_t('Transaction was timed out on the payment terminal. Please retry.'));
                    if(line && line.set_payment_status){
                        line.set_payment_status('force_done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve();
                } else if (response.responseCode == 'B5' && response.responseText.includes('Invalid Amount')){
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    self._show_error(_t('Invalid Amount'));
                    if(line && line.set_payment_status){
                        line.set_payment_status('force_done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve();
                } else if (response.responseCode == 'BY' && response.responseText.includes('PINpad Busy')){
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    self._show_error(_t('The payment terminal is processing another payment. Please wait and try again'));
                    if(line && line.set_payment_status){
                        line.set_payment_status('force_done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve();
                } else if (response.responseCode == '70' && response.responseText.includes('SYSTEM ERROR')){
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    self._show_error(_t('Unable to process payment due to some system error.'));
                    if(line && line.set_payment_status){
                        line.set_payment_status('force_done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve();
                } else if (response.responseCode == 'PF' && response.responseText.includes('PINpad Offline"')){
                    var line = self.pending_linkly_line() || Promise.resolve(false);
                    self._show_error(_t('Unable to process payment as the PINpad is Offline.'));
                    if(line && line.set_payment_status){
                        line.set_payment_status('force_done');
                        line.fail_transaction = false
                    }
                    return Promise.resolve();
                } else {
                    console.log("reject : ",response)
                    self.poll_error_order = self.pos.getOrder();
                    return Promise.reject();
                    return self._handleOdooConnectionFailure(response);
                }
            } else {
                var line = this.pending_linkly_line();
                this._show_error(_t(response.title));
                if(line && line.set_payment_status){
                    line.set_payment_status('force_done');
                }
                return Promise.resolve();

            }
        } else {
            console.log("reject : ",response)
            self.poll_error_order = self.pos.getOrder();
            return false;
            // return self._handleOdooConnectionFailure(response);
        }
    }
    _show_error (msg, title) {
        if (!title) { title =  _t('EFTPOS Error') }

        this.env.services.dialog.add(AlertDialog, {
            'title': title,
            'body': msg || 'An unexpected error occurred. Message ',
        });
    }
}
