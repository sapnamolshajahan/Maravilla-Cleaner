/** @odoo-module */

import { PosStore } from "@point_of_sale/app/store/pos_store";
import { PosOrder } from "@point_of_sale/app/models/pos_order";
import { patch } from "@web/core/utils/patch";
import { utils  } from "@web/core/ui/ui_service";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { _t } from "@web/core/l10n/translation";

patch(PosStore.prototype, {
    // @Override

    async processServerData() {
        await super.processServerData();
        console.log("____this",this)
        this.pos_loyalty_setting = this.data.models['all.loyalty.setting'].getAll();
        this.pos_redeem_rule = this.data.models['all.redeem.rule'].getAll();
        
    },


    get_total_loyalty_pts(){
    	console.log("____get_total_loyalty_pts____")
		let round_pr = utils.round_precision;
		let round_di = utils.round_decimals;
		let rounding = this.currency.rounding;
		let final_loyalty = 0
		let order = this.get_order();
		let orderlines = order.get_orderlines();
		let partner_id = order.get_partner();
		if(this.pos_loyalty_setting.length != 0){				
		   if (this.pos_loyalty_setting[0].loyalty_basis_on == 'loyalty_category') {
				if (partner_id){
					let loyalty = 0;
					for (let i = 0; i < orderlines.length; i++) {
						let lines = orderlines[i];
						let cat_ids = lines.product_id.bi_pos_reports_catrgory
						if(cat_ids){
							if (cat_ids['Minimum_amount']>0){
								final_loyalty += lines.get_price_with_tax() / cat_ids['Minimum_amount'];
							}
						}
					}
					order.set_final_loyalty(final_loyalty)
					return parseFloat(final_loyalty.toFixed(2));
				}
		   }else if (this.pos_loyalty_setting[0].loyalty_basis_on == 'amount') {
				let loyalty_total = 0;
				if (order && partner_id){
					let amount_total = order.get_total_with_tax();
					let subtotal = order.get_total_without_tax();

				    // Remove delivery lines from amount paid that is valid for redeeming points
					let amount_loyalty_valid = 0;
					console.log(orderlines);
//
					for (let i = 0; i < orderlines.length; i++) {
						let lines = orderlines[i];
						let is_delivery = lines.product_id.is_delivery;
						console.log(lines.product_id.is_delivery);
						console.log(lines.product_id);
						if(!is_delivery){
                            amount_loyalty_valid += lines.get_price_with_tax();
						}
					}

					let loyaly_points = this.pos_loyalty_setting[0].loyality_amount;
					final_loyalty += (amount_loyalty_valid / loyaly_points);
					if(order.get_partner()){
						loyalty_total = order.get_partner().loyalty_points1 + final_loyalty;							
					}
					console.log("--vvvv",final_loyalty)
					order.set_final_loyalty(final_loyalty)
					return parseFloat(final_loyalty.toFixed(2));
				}
			}
		}

		
		return parseFloat(final_loyalty.toFixed(2));
	},

    async selectPartner() {
        // FIXME, find order to refund when we are in the ticketscreen.
        const currentOrder = this.get_order();
        if(currentOrder.redeem_done){
			this.env.services.popup.add(ErrorPopup,{
				title: _t('Cannot Change Customer'),
				body: _t('Sorry, you redeemed product, please remove it before changing customer.'),
			}); 
		}else{
			super.selectPartner();
		}
    }
   
});

patch(PosOrder.prototype, {
    setup() {
        super.setup(...arguments);
        this.loyalty = this.loyalty  || 0;
		this.redeemed_points = this.redeemed_points || 0;
		this.redeem_done = this.redeem_done || false;
		this.remove_true = this.remove_true || false;
		this.redeem_point = this.redeem_point || 0;
		this.remove_line = this.remove_line || false;
		this.final_loyalty = this.get_final_loyalty() || 0;
    },
   

	removeOrderline(line) {
        this.redeem_done = false;
        if(line.id ==this.remove_line){
			this.remove_true = true;
			let partner = this.get_partner();
			if (partner) {
				partner.loyalty_points1 = partner.loyalty_points1 + parseFloat(this.redeem_point) ;
			}
		}
		else{
			this.remove_true = false;
		}
        super.removeOrderline(line);
    },
	get_redeemed_points(){
		return this.redeemed_points;
	},


	set_final_loyalty(final_loyalty){
		console.log("______final_loyalty",final_loyalty)
		this.final_loyalty = final_loyalty
	},

	get_final_loyalty(){
		return this.final_loyalty;
	},

	

	export_for_printing() {
        const result = super.export_for_printing(...arguments);
        result.total_loyalty = this.get_final_loyalty();
        return result;
    },
});
