from odoo import models


class DummyERPExportMixin(models.AbstractModel):
    """ Simple mixin, that defines functions needed to export odoo object as dummy erp object

        class MyModel:
            _name = 'my.model'
            _inherit = 'dummy.erp.export.mixin'
    """
    _name = 'dummy.erp.export.mixin'
    _description = 'Dummy ERP Export Mixin'
