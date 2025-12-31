import { Dialog } from "@web/core/dialog/dialog";
import { usePos } from "@point_of_sale/app/store/pos_hook";
import { Component, useState } from "@odoo/owl";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
let redeem;
export class LoyaltyPopupWidget extends Component {
    static template = "sale_pos_ecomm_loyalty.LoyaltyPopupWidget";
    static components = { Dialog };
    static props = {
    	close: Function,
    	partner: Object,
    };
    setup() {
        this.pos = usePos();
        this.loyalty_settings = this.pos.pos_loyalty_setting;
		this.calculate_loyalty_points();
    }
    


    calculate_loyalty_points(){
		let self = this;
		let order = this.pos.get_order();
		let orderlines = order.get_orderlines();
		let partner = this.props.partner;
		
		
		self.partner = partner || {};
		self.loyalty = partner.loyalty_pts;

		if(this.loyalty_settings.length != 0){
			if(this.loyalty_settings[0].redeem_ids.length != 0){
				let redeem_arr = []
				for (let i = 0; i < this.loyalty_settings[0].redeem_ids.length; i++) {
					
					for (let j = 0; j < this.pos.pos_redeem_rule.length; j++) {

						console.log("---ffff----this")
						if(self.loyalty_settings[0].redeem_ids[i].id == self.pos.pos_redeem_rule[j].id){
							redeem_arr.push(self.pos.pos_redeem_rule[j]);
						}
					}
				}
				for (let j = 0; j < redeem_arr.length; j++) {
					if( redeem_arr[j].min_amt <= partner.loyalty_pts && partner.loyalty_pts <= redeem_arr[j].max_amt)
					{
						redeem = redeem_arr[j];
						break;
					}
				}
				console.log("---redeem-----v",redeem);
				if(redeem){
					let point_value = redeem.reward_amt * self.loyalty;
					console.log("______point_value",point_value)
					if (partner){
						self.loyalty_amount = point_value;
						partner.loyalty_amount = point_value;
					}
				}
			}
		}
	}

	async redeemPoints() {
		let self = this;
		let order = this.pos.get_order();
		let orderlines = order.get_orderlines();
		var entered_code = document.getElementById("entered_item_qty").value
		let point_value = 0;
		let remove_line;	
		let partner = this.props.partner;
		let loyalty = partner.loyalty_pts;

		if(this.loyalty_settings.length != 0){
		    console.log(this.loyalty_settings[0])
			let product_id = this.loyalty_settings[0].product_id.id;
			this.product = this.pos.models['product.product'].getBy('id',product_id);
			if(!this.product){
				this.pos.dialog.add(AlertDialog, {
                    title: _t('Product Not Found'),
                    body: _t('Please, set the Loyalty Product Available in POS.'),
                });
                self.props.close();
            	return 
            }
        }
		if(entered_code<0)
		{
			alert('Please enter valid amount.');
			return
		}
		if(redeem && redeem.min_amt <= loyalty &&  loyalty<= redeem.max_amt)
		{
			if(entered_code <= loyalty)
			{
				let total = order.get_total_with_tax();
				let redeem_value = redeem.reward_amt * entered_code
				if (redeem_value > total) {
					alert('Please enter valid amounts.')
				}
				if (redeem_value <= total) {

						const line = await this.pos.addLineToCurrentOrder({
			                product_id: self.product,
			                price_unit: - redeem_value,
			                
			            });
						// order.add_product(this.product, {
						// 	price: -redeem_value
						// });
						partner.loyalty_pts -= entered_code;
						remove_line = orderlines[orderlines.length-1].id
						order.redeemed_points = entered_code;
						order.redeem_done = true;
						order.redeem_point = entered_code;
						order.remove_line = remove_line;
						self.props.close();
				}
					// else{
					// 	alert('Please set loyalty product at Point Of Sale Configuration.')
					// }
				// }
			}
			else{
				alert('Please enter valid amount.');
			}
		}
		else{
			alert("limit exceeded");
		}	
				  
	}

}
