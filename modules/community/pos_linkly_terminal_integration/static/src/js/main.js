/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* License URL : <https://store.webkul.com/license.html/> */
import { PosPayment } from "@point_of_sale/app/models/pos_payment";
import { patch } from "@web/core/utils/patch";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";
import { _t } from "@web/core/l10n/translation";
import { ConfirmationDialog, AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { register_payment_method } from "@point_of_sale/app/services/pos_store";
import { LINKLY } from '@pos_linkly_terminal_integration/js/payment_linkly';
import { PaymentScreenPaymentLines } from "@point_of_sale/app/screens/payment_screen/payment_lines/payment_lines";
import { TicketScreen } from "@point_of_sale/app/screens/ticket_screen/ticket_screen";

register_payment_method('linkly', LINKLY);

patch(TicketScreen.prototype, {  
  async setTxn(selected_order){
    try {
      const result = await this.env.services.orm.call("linkly.transaction", "search_read", [], {
        domain: ['|',["order_ref","=",selected_order.pos_reference],["order_ref","=",selected_order.name]],
        fields: ["id","txnRef"],
        limit: 1,
      });  
      return result;
    } catch (error) {
      console.error("Error fetching linkly transaction:", error);
    }
  },
  async onDoRefund() {
    await super.onDoRefund();
    const selected_order = this.getSelectedOrder();
    const result = await this.setTxn(selected_order);
    let order = this.pos.getOrder();
    if (order && result && result.length){
      order.update({txnRef: result[0].txnRef})
    }
  }
});

patch(PosPayment.prototype, {
  setup(vals) {
    super.setup(...arguments);
    this.status = vals.status || false;
    this.linkly_receipt = vals.linkly_receipt || false;
    this.payment_status = vals.payment_status || false;
    this.linkly_payment_UUID = vals.linkly_payment_UUID || false;
    this.fail_transaction = vals.fail_transaction || false;
    this.txnRef = vals.txnRef || false;    
  },
  setTerminalServiceId(id) {
    this.terminalServiceId = id;
  }
});

patch(PosOrder, {
  extraFields: {
    ...(PosOrder.extraFields || {}),
    txnRef: {
      model: "pos.order",
      name: "txnRef",
      type: "char",
      local: true,
    },
  },
});

patch(PosOrder.prototype, {
  setup(vals) {
    super.setup(...arguments);
    this.txnRef = vals.txnRef || false;
  },
});

patch(PaymentScreenPaymentLines.prototype, {
  async clickWkLinklyReprint(line, operation = false){
    var data = { 'txnRef': line.txnRef }
    return this.pos.data.call("pos.payment.method", "reprint_linkly_receipt", [data])
      .catch(this._handleOdooConnectionFailure.bind(this));
  },
  _handleOdooConnectionFailure(data){
    return Promise.reject(data)
  },
});

patch(PaymentScreen.prototype, {
  setup(){
    super.setup();
  },
  async addNewPaymentLine(paymentMethod) {
    if(paymentMethod.use_payment_terminal == "linkly" && !paymentMethod.secret){
      this.dialog.add( AlertDialog, {
          title: ('Configuration Error'),
          body: ('Please complete the PIN PAD Pairing Process for this payment method to use in this POS.'),
      });
      return true;
    } else {
        return super.addNewPaymentLine(paymentMethod);
    }
  },
  async clickBackPaymentPage() {
    var self = this;
    var payment_lines = self.pos.getOrder().payment_ids;
    var linkly_payment_exist = false
    payment_lines.forEach(function (line) {
      if(line.payment_method_id && line.payment_method_id.use_payment_terminal && line.payment_method_id.use_payment_terminal == "linkly"){
        if(line.payment_status == 'waiting' || line.payment_status == 'retry'){
          linkly_payment_exist = true
        }
      }
    });
    if(linkly_payment_exist){
      var {confirmed, payload} = await this.dialog.add(ConfirmationDialog, {
        title: _t('Pending Payment'),
        body: _t('There are pending payments. If you go to another screen it could result in loss of payment data.'),
      });
      if(!confirmed)
        return;
    }
    var lines = self.pos.getOrder().get_orderlines();
    lines.forEach(function (line) {
      if (line.line_discount) {
        line.set_discount(0);
        line.line_discount = false;
      }
    });
    self.pos.showScreen("ProductScreen");
  }
});
