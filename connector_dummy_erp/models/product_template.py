import base64
import requests

from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"
    """
    We apply all operations on product template since the other ERP does not have attributes/variants, and whenever
    we need variant-specific attributes we use the product_variant_id field from product.template.
    """

    dummy_erp_integration_id = fields.Many2one("dummy.erp.integration", ondelete="restrict")
    dummy_erp_id = fields.Integer("ID In Dummy ERP")
    dummy_erp_brand = fields.Char("Dummy ERP Brand")
    dummy_erp_rating = fields.Float("Rating")
    discount_percentage = fields.Float("Discount Percentage")

    @api.model
    def get_products_updated_after_last_write(self, last_write):
        products = self.search([("write_date", "<=", last_write)])
        return self.prepare_dummy_erp_payload(products)

    @api.model
    def prepare_dummy_erp_payload(self, recs):
        payload = []
        base_url = self.get_base_url()
        for rec in recs:
            payload.append({
                "id": rec.product_variant_id.id,
                "title": rec.name,
                "description": rec.description_sale or "",
                "price": rec.list_price,
                "discountPercentage": rec.discount_percentage or 0.0,
                "rating": rec.dummy_erp_rating or 0.0,
                "stock": rec.product_variant_id.qty_available,
                "brand": rec.dummy_erp_brand,
                "category": rec.product_categ_id.name,
                "thumbnail": base_url + f'/web/image/product.template/{rec.id}/image_128',
                "images": [
                    base_url + f'/web/image/product.template/{rec.id}/image_128',
                    base_url + f'/web/image/product.template/{rec.id}/image_256',
                    base_url + f'/web/image/product.template/{rec.id}/image_512',
                    base_url + f'/web/image/product.template/{rec.id}/image_1024',
                    base_url + f'/web/image/product.template/{rec.id}/image_1920'
                ]
            })
        return payload

    @api.model
    def create_or_update_from_dummy_erp_payload(self, integration_id, payload):
        products = self.prepare_dicts_from_dummy_erp_payload(integration_id, payload)
        for product_dict in products:
            if product_dict["id"]:
                product_obj = self.search(
                    [("dummy_erp_id", "=", product_dict["id"])], limit=1
                )
                product_dict.pop('id')
                if product_obj:
                    product_obj.write(product_dict)
                else:
                    self.create(product_dict)

    @api.model
    def prepare_dicts_from_dummy_erp_payload(self, integration_id, payload):
        product_dicts = []
        for product in payload:
            image_1920 = False
            if len(product["images"]) > 0:
                image_1920 = base64.b64encode(requests.get(product["images"][0]).content)
            product_dicts.append({
                "id": product["id"],
                "name": product["title"],
                "list_price": product["price"],
                "description_sale": product["description"],
                "taxes_id": integration_id.default_tax_ids.ids,
                "dummy_erp_rating": product["rating"],
                "dummy_erp_brand": product["brand"],
                "dummy_erp_id": product["id"],
                "dummy_erp_integration_id": integration_id.id,
                "image_1920": image_1920,
            })
        return product_dicts
