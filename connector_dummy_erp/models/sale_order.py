from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = ["sale.order"]

    def _dummy_erp_default_website(self):
        """ Find the first company's website, if there is one. """
        company_id = self.env.company.id

        if self._context.get('default_company_id'):
            company_id = self._context.get('default_company_id')

        domain = [('company_id', '=', company_id)]
        return self.env['website'].search(domain, limit=1)

    dummy_erp_integration_id = fields.Many2one("dummy.erp.integration", ondelete="restrict")
    dummy_erp_id = fields.Integer("ID In Dummy ERP")

    # Indicating whether this order should be updated in the dummy ERP. By default, created orders should be synced.
    update_to_dummy_erp = fields.Boolean(default=True)

    @api.model
    def get_carts_to_update(self):
        products = self.search([("update_to_dummy_erp", "=", True)])
        return self.prepare_dummy_erp_payload(products)

    @api.model
    def prepare_dummy_erp_payload(self, recs):
        payload = []
        for rec in recs:
            lines = []
            user_id = rec.partner_id.user_ids[0]
            for sol in rec.order_line:
                if sol.product_id.dummy_erp_id:
                    lines.append(
                        {
                            "id": sol.product_id.dummy_erp_id,
                            "price": sol.price_unit,
                            "quantity": sol.product_uom_qty,
                            "discountPercentage": sol.discount,
                        }
                    )
            payload.append({
                "id": rec.dummy_erp_id,
                "userId": user_id.dummy_erp_id,
                "cart_obj": rec,
                "products": lines
            })
        return payload

    @api.model
    def create_from_dummy_erp_payload(self, user_id, integration_id, carts):
        for cart in carts:
            if not self.search([("dummy_erp_id", "=", cart["id"])], limit=1):
                lines = []
                for item in cart["products"]:
                    product_id = self.env["product.template"].get_product_id_by_dummy_erp_id(
                        item["id"]
                    )
                    if product_id:
                        line_price = item["price"]
                        line_discount = item["discountPercentage"]
                        line_quantity = item["quantity"]
                        lines.append(
                            [
                                0,
                                0,
                                {
                                    "product_id": product_id.id,
                                    "product_uom_qty": line_quantity,
                                    "price_unit": line_price,
                                    "discount": line_discount,
                                },
                            ]
                        )
                    else:
                        continue

                website_id = self._dummy_erp_default_website()
                self.env["sale.order"].create({
                    "partner_id": user_id.partner_id.id,
                    "partner_invoice_id": user_id.partner_id.id,
                    "dummy_erp_id": cart["id"],
                    "website_id": website_id.id,
                    "dummy_erp_integration_id": integration_id.id,
                    "order_line": lines,
                })
