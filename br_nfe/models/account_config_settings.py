# -*- coding: utf-8 -*-
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# © 2017 Michell Stuttgart <michellstut@gmail.com>, MultidadosTI
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class AccountConfigSettings(models.TransientModel):
    _inherit = 'account.config.settings'

    nfe_email_template = fields.Many2one('mail.template',
                                         string='Template de Email para NFe',
                                         domain=[('model_id.model', '=', 'invoice.electronic')])  # noqa

    def get_default_nfe_email_template(self, fields):
        """ Atribui ao campo 'nfe_email_template' o valor default retornado
        abaixo .

        :param fields:
        :rtype: dict
        :return: Dict com os campos e seus respectivos valores default
        """
        return {
            'nfe_email_template':
                self.env.user.company_id.nfe_email_template.id,
        }

    @api.multi
    def set_default_nfe_email_template(self):
        """ Quando atribuimos um valor ao campo 'nfe_email_template', este
        mesmo valor é atribuido ao campo correspondente no cadastro da empresa.
        """
        self.env.user.company_id.nfe_email_template = self.nfe_email_template
