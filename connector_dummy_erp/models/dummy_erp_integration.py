from odoo import models, fields, api, _
from odoo.exceptions import UserError

from .api_client import send_request

DUMMY_JSON_PATHS = {
    "test": "/test",
    "get_products": "/products?limit=0",
    "get_carts": "/carts?limit=0",
    "get_users": "/users?limit=0",
    "update_cart": "/carts",
    "update_product": "/products",
    "add_product": "/products/add"
}


class DummyERPIntegration(models.Model):
    _name = 'dummy.erp.integration'
    _description = 'Dummy ERP Integration'
    _inherit = ['mail.thread']

    # Default values computation methods
    def _default_pricelist(self):
        return self.env['product.pricelist'].search([('company_id', 'in', (False, self.env.company.id)),
                                                     ('currency_id', '=', self.env.company.currency_id.id)],
                                                    limit=1)

    # Basic integration fields
    name = fields.Char("Name", required=1)
    active = fields.Boolean("Active", default=False, tracking=True)
    base_url = fields.Char("Base Integration URL", default="https://dummyjson.com")

    # Automation fields
    auto_import_product = fields.Boolean("Auto Import Products", default=False, tracking=True)
    auto_import_user = fields.Boolean("Auto Import Users", default=False, tracking=True)
    auto_export_cart = fields.Boolean("Auto Export Carts", default=False, tracking=True)
    auto_export_product = fields.Boolean("Auto Export Products", default=False, tracking=True)
    # TODO: When automation values are changed; apply changes to the relevant cron job

    last_export_cart = fields.Datetime("Last Import Products")
    last_export_product = fields.Datetime("Last Import Products")

    # Cron IDS
    import_product_cron_id = fields.Many2one("ir.cron")
    import_user_cron_id = fields.Many2one("ir.cron")
    export_cart_cron_id = fields.Many2one("ir.cron")
    export_product_cron_id = fields.Many2one("ir.cron")

    # Smart buttons
    cron_ids = fields.One2many(
        "ir.cron", "dummy_erp_integration_id", context={"active_test": False}
    )
    cron_count = fields.Integer("Jobs", compute="_compute_cron_count")
    integration_log_ids = fields.One2many("dummy.erp.integration.log", "integration_id")

    # Business logic fields
    pricelist_id = fields.Many2one("product.pricelist", "Pricelist", default=_default_pricelist, tracking=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company.id)
    default_tax_ids = fields.Many2many("account.tax", string="Default Taxes", domain=[('type_tax_use', '=', 'sale')],
                                       tracking=True)

    ##################
    # Helper methods
    ##################
    def _get_base_url(self):
        self.ensure_one()
        if self.base_url[-1] == "/":
            return self.base_url[0:-1]
        else:
            return self.base_url

    def log_operation(self, subject, details, type):
        self.env["dummy.erp.integration.log"].sudo().create(
            {
                "integration_id": self.id,
                "name": subject,
                "details": details,
                "type": type,
            }
        )

    ######################
    # View records methods
    ######################
    def action_view_crons(self):
        action = self.env["ir.actions.actions"]._for_xml_id("base.ir_cron_act")
        action.update({"domain": [("dummy_erp_integration_id", "=", self.id)]})
        return action

    def _compute_cron_count(self):
        for rec in self:
            rec.cron_count = len(rec.cron_ids)

    def action_view_log(self):
        action = self.env["ir.actions.actions"]._for_xml_id(
            "connector_dummy_erp.act_window_dummy_erp_log"
        )
        action.update({"domain": [("integration_id", "=", self.id)]})
        return action

    ################################################################
    # Technical methods
    ################################################################

    # Override create to create crons simultaneously
    @api.model
    def create(self, vals):
        res = super(DummyERPIntegration, self).create(vals)
        res._create_dummy_erp_product_importer()
        res._create_dummy_erp_user_importer()
        res._create_dummy_erp_cart_exporter()
        res._create_dummy_erp_product_exporter()
        return res

    def toggle_active(self):
        res = super(DummyERPIntegration, self).toggle_active()
        if self.active:
            self.cron_ids.write({"active": True})
        else:
            self.cron_ids.write({"active": False})
        return res

    def test_connection(self):
        try:
            response = send_request(self, "GET", {}, DUMMY_JSON_PATHS["test"])
            if 200 <= response.status_code < 300 and response.json()["status"]:
                message = _("Connection Test Successful!")
                self.log_operation(
                    _("Test Connection"),
                    message,
                    "info",
                )
                return {
                    "type": "ir.actions.client",
                    "tag": "display_notification",
                    "params": {
                        "message": message,
                        "type": "success",
                        "sticky": False,
                    },
                }
            elif response.json()["status"] == "error":
                message = response.json()["message"]["description"]
                self.log_operation(
                    _("Test Connection"),
                    message,
                    "error",
                )
                raise UserError(
                    _("The server refused the test connection with error: ") + message
                )
        except Exception as e:
            self.log_operation(
                _("Test Connection"),
                str(e),
                "error",
            )
            raise UserError(
                _("An error occurred testing connection: ") + str(e)
            )

    def _create_dummy_erp_product_importer(self):
        """
        Creates a new cron job which runs import products with the id of this object.
        """
        model_id = self.env["ir.model"].search([("model", "=", self._name)])
        cron_id = self.env["ir.cron"].create(
            dict(
                name=f"Dummy ERP Integration {self.name}: Import Products",
                model_id=model_id.id,
                interval_number=20,
                interval_type="minutes",
                active=False,
                numbercall=-1,
                state="code",
                code=f"model.import_dummy_products({self.id})",
            )
        )
        self.import_product_cron_id = cron_id.id
        cron_id.dummy_erp_integration_id = self

    def _create_dummy_erp_user_importer(self):
        """
        Creates a new cron job which runs import users with the id of this object.
        """
        model_id = self.env["ir.model"].search([("model", "=", self._name)])
        cron_id = self.env["ir.cron"].create(
            dict(
                name=f"Dummy ERP Integration {self.name}: Import Users",
                model_id=model_id.id,
                interval_number=20,
                interval_type="minutes",
                active=False,
                numbercall=-1,
                state="code",
                code=f"model.import_dummy_users({self.id})",
            )
        )
        self.import_user_cron_id = cron_id.id
        cron_id.dummy_erp_integration_id = self

    def _create_dummy_erp_cart_exporter(self):
        """
        Creates a new cron job which runs export carts with the id of this object.
        """
        model_id = self.env["ir.model"].search([("model", "=", self._name)])
        cron_id = self.env["ir.cron"].create(
            dict(
                name=f"Dummy ERP Integration {self.name}: Export Carts",
                model_id=model_id.id,
                interval_number=2,
                interval_type="minutes",
                active=False,
                numbercall=-1,
                state="code",
                code=f"model.export_dummy_carts({self.id})",
            )
        )
        self.export_cart_cron_id = cron_id.id
        cron_id.dummy_erp_integration_id = self

    def _create_dummy_erp_product_exporter(self):
        """
        Creates a new cron job which runs export products with the id of this object.
        """
        model_id = self.env["ir.model"].search([("model", "=", self._name)])
        cron_id = self.env["ir.cron"].create(
            dict(
                name=f"Dummy ERP Integration {self.name}: Export Products",
                model_id=model_id.id,
                interval_number=2,
                interval_type="minutes",
                active=False,
                numbercall=-1,
                state="code",
                code=f"model.export_dummy_products({self.id})",
            )
        )
        self.export_product_cron_id = cron_id.id
        cron_id.dummy_erp_integration_id = self

    ##########################
    # Business Logic methods: Importers
    ##########################
    @api.model
    def import_dummy_products(self, integration_id):
        integration = self.with_context(active_test=False).search([("id", "=", integration_id)])
        try:
            response = send_request(integration, "GET", {}, DUMMY_JSON_PATHS["get_products"])
            if (
                    200 <= response.status_code < 300
                    and "products" in response.json()
                    and len(response.json()["products"]) > 0
            ):
                payload = response.json()["products"]
                self.env["product.template"].create_or_update_from_dummy_erp_payload(
                    integration, payload
                )
                integration.log_operation(
                    _("Import Products"),
                    (
                        f"Products batch imported successfully {response.json()['products']}"
                    ),
                    "info",
                )
                self.env.cr.commit()

        except Exception as exc:
            integration.log_operation(
                _("Import Products"),
                (f"Exception: {str(exc)}"),
                "error",
            )

    @api.model
    def import_dummy_users(self, integration_id):
        integration = self.with_context(active_test=False).search([("id", "=", integration_id)])
        pass

    ##########################
    # Business Logic methods: Exporters
    ##########################
    @api.model
    def export_dummy_products(self, integration_id):
        integration = self.with_context(active_test=False).search([("id", "=", integration_id)])
        pass

    @api.model
    def export_dummy_carts(self, integration_id):
        integration = self.with_context(active_test=False).search([("id", "=", integration_id)])
        pass
