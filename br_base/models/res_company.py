# © 2004-2010 Tiny SPRL (<http://tiny.be>)
# © Thinkopen Solutions (<http://www.thinkopensolutions.com.br>)
# © Akretion (<http://www.akretion.com>)
# © KMEE (<http://www.kmee.com.br>)
# © 2016 Danimar Ribeiro <danimaribeiro@gmail.com>, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).


import base64
import logging
import re
from datetime import datetime

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

try:
    from OpenSSL import crypto
except ImportError:
    _logger.debug('Cannot import OpenSSL.crypto', exc_info=True)


class ResCompany(models.Model):
    _inherit = 'res.company'

    @api.multi
    def _get_address_data(self):
        for company in self:
            company.city_id = company.partner_id.city_id
            company.district = company.partner_id.district
            company.number = company.partner_id.number

    @api.multi
    def _get_br_data(self):
        """ Read the l10n_br specific functional fields. """
        for company in self:
            company.legal_name = company.partner_id.legal_name
            company.cnpj_cpf = company.partner_id.cnpj_cpf
            company.inscr_est = company.partner_id.inscr_est
            company.inscr_mun = company.partner_id.inscr_mun
            company.suframa = company.partner_id.suframa

    @api.multi
    def _set_br_suframa(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.suframa = company.suframa

    @api.multi
    def _set_br_legal_name(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.legal_name = company.legal_name

    @api.multi
    def _set_br_cnpj_cpf(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.cnpj_cpf = company.cnpj_cpf

    @api.multi
    def _set_br_inscr_est(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_est = company.inscr_est

    @api.multi
    def _set_br_inscr_mun(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.inscr_mun = company.inscr_mun

    @api.multi
    def _set_br_number(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.number = company.number

    @api.multi
    def _set_br_district(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.district = company.district

    @api.multi
    def _set_city_id(self):
        """ Write the l10n_br specific functional fields. """
        for company in self:
            company.partner_id.city_id = company.city_id

    @api.multi
    def _compute_expiry_date(self):
        for company in self:

            try:
                pfx = base64.decodestring(
                    self.with_context(bin_size=False).nfe_a1_file)
                pfx = crypto.load_pkcs12(pfx, company.nfe_a1_password)
                cert = pfx.get_certificate()
                end = datetime.strptime(cert.get_notAfter(), '%Y%m%d%H%M%SZ')
                subj = cert.get_subject()
                company.cert_expire_date = end

                if datetime.now() < end:
                    company.cert_state = 'valid'
                else:
                    company.cert_state = 'expired'
                    company.cert_information = "%s\n%s\n%s\n%s" % (subj.CN, subj.L, subj.O, subj.OU)  # noqa

            except crypto.Error:
                company.cert_state = 'invalid_password'
            except Exception:
                company.cert_state = 'unknown'
                _logger.error('Erro desconhecido ao consultar certificado',
                              exc_info=True)

    cnpj_cpf = fields.Char(compute=_get_br_data,
                           inverse=_set_br_cnpj_cpf,
                           size=18,
                           string='CNPJ')

    inscr_est = fields.Char(compute=_get_br_data,
                            inverse=_set_br_inscr_est,
                            size=16,
                            string='Inscr. Estadual')

    inscr_mun = fields.Char(compute=_get_br_data,
                            inverse=_set_br_inscr_mun,
                            size=18,
                            string='Inscr. Municipal')

    suframa = fields.Char(compute=_get_br_data,
                          inverse=_set_br_suframa,
                          size=18,
                          string='Suframa')

    legal_name = fields.Char(compute=_get_br_data,
                             inverse=_set_br_legal_name,
                             size=128,
                             string='Razão Social')

    city_id = fields.Many2one(compute=_get_address_data,
                              inverse='_set_city_id',
                              comodel_name='res.state.city',
                              string="City",
                              multi='address')

    district = fields.Char(compute=_get_address_data,
                           inverse='_set_br_district',
                           size=32,
                           string='Bairro',
                           multi='address')

    number = fields.Char(compute=_get_address_data,
                         inverse='_set_br_number',
                         size=10,
                         string='Número',
                         multi='address')

    nfe_a1_file = fields.Binary('Arquivo NFe A1')
    nfe_a1_password = fields.Char('Senha NFe A1', size=64)

    cert_state = fields.Selection([('not_loaded', 'Não carregado'),
                                   ('expired', 'Expirado'),
                                   ('invalid_password', 'Senha Inválida'),
                                   ('unknown', 'Desconhecido'),
                                   ('valid', 'Válido')],
                                  string='Situação Cert.',
                                  compute=_compute_expiry_date,
                                  default='not_loaded')

    cert_information = fields.Text(string='Informações Cert.',
                                   compute=_compute_expiry_date)

    cert_expire_date = fields.Date(string='Validade Cert.',
                                   compute=_compute_expiry_date)

    @api.onchange('cnpj_cpf')
    def onchange_mask_cnpj_cpf(self):
        for company in self:
            if company.cnpj_cpf:
                val = re.sub('[^0-9]', '', company.cnpj_cpf)
                if len(val) == 14:
                    company.cnpj_cpf = "%s.%s.%s/%s-%s" % (val[0:2], val[2:5], val[5:8], val[8:12], val[12:14])  # noqa: 501

    @api.onchange('city_id')
    def onchange_city_id(self):
        """ Ao alterar o campo city_id copia o nome
        do município para o campo city que é o campo nativo do módulo base
        para manter a compatibilidade entre os demais módulos que usam o
        campo city.
        """
        for company in self:
            if company.city_id:
                company.city = company.city_id.name

    @api.onchange('zip')
    def onchange_mask_zip(self):
        for company in self:
            if company.zip:
                val = re.sub('[^0-9]', '', company.zip)
                if len(val) == 8:
                    company.zip = "%s-%s" % (val[0:5], val[5:8])
