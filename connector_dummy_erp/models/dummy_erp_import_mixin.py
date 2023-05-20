from odoo import models


class DummyERPImportMixin(models.AbstractModel):
    """ Simple mixin, that defines functions needed to import dummy erp object as odoo object

        class MyModel:
            _name = 'my.model'
            _inherit = 'dummy.erp.import.mixin'
    """
    _name = 'dummy.erp.import.mixin'
    _description = 'Dummy ERP Import Mixin'
