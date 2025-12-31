/** @odoo-module */

import { register_payment_method } from "@point_of_sale/app/store/pos_store";
import { PaymentSmartPay } from "@pos_smartpay/js/payment-smartpay";

register_payment_method('smartpay', PaymentSmartPay);
