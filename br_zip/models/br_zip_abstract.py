# © 2018 Michell Stuttgart, Multidados
import re
import logging
import urllib3

from pycep_correios import PRODUCAO, consultar_cep
from pycep_correios.excecoes import (CEPInvalido,
                                     ExcecaoPyCEPCorreios,
                                     FalhaNaConexao)

from odoo import api, models
from odoo.exceptions import UserError
from odoo.tools.translate import _

# Desabilita warnig da request durante a consulta do cep
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

_logger = logging.getLogger(__name__)


class BrZipAbstract(models.AbstractModel):
    _name = 'br.zip.abstract'
    _description = 'Abstract class to add zip search'

    @api.onchange('zip')
    def _onchange_zip(self):
        """Realiza a busca dos dados de endereço de acordo com
        o CEP inserido.
        """
        cep = re.sub('[^0-9]', '', self.zip or '')
        if len(cep) == 8:
            self.zip = "%s-%s" % (cep[0:5], cep[5:8])
            self.update(self.get_address())

    @api.multi
    def get_address_from_zip(self, zip_code, environment):
        """Realiza a consulta de CEP no webservice de dos Correios
        de acordo com o ambiente escolhido e retorna os dados do
        endereço relativo ao CEP.

        Arguments:
            zip_code {str} -- Código do CEP para consulta
            environment {int} -- Constante que indica o ambiente da consulta.

        Raises:
            UserError -- Quando o CEP não é valido
            UserError -- Quando ocorre erro na conexão com o Webservice

        Returns:
            dict -- Dados dos endereços buscado.
                zip_code {str} -- codigo do cep
                street {str} -- nome do logradouro
                district {str} -- nome do bairro
                city {str} -- nome da cidade
                state_code {str} -- código do estado, i.e, 'MG', 'SP" e etc
                country_code {str} -- código do país, i.e, 'BR'
        """

        try:
            res = consultar_cep(zip_code, ambiente=environment)

            values = {
                'zip_code': res['cep'],
                'street': res['end'],
                'district': res['bairro'],
                'city': res['cidade'],
                'state_code': res['uf'],
                'country_code': 'BR',
            }

            return values

        except CEPInvalido as exc:
            _logger.error(exc, exc_info=True)
            raise UserError(_('CEP inválido'))

        except FalhaNaConexao as exc:
            _logger.error(exc, exc_info=True)
            raise UserError(('Falha na comunicação com os Correios. \
            Tente novamente mais tarde.'))

        except ExcecaoPyCEPCorreios as exc:
            _logger.error(exc, exc_info=True)
            raise UserError(
                _('Ocorreu um erro desconhecido. \
                Contate o administrado do sistema'))

        except Exception as exc:
            _logger.error(exc, exc_info=True)
            raise UserError(
                _('Ocorreu um erro desconhecido. \
                Contate o administrado do sistema'))

    @api.multi
    def create_br_zip_from_address(self, zip_code, street, district, city, state_code, country_code):
        """Cria um objeto br.zip a partir dos parametros fornecidos.

        Arguments:
            zip_code {str} -- Codigo de CEP
            street {str} -- Nome do logradouro
            district {str} -- Nome do bairro
            city {str} -- Nome da cidade
            state_code {str} -- Codigo do estado
            country_code {str} -- Codigo do país

        Returns:
            BrZip -- Nova instancia de br.zip
        """

        values = {
            'zip': zip_code,
            'street': street,
            'district': district,
        }

        # Search Brazil id
        country_ids = self.env['res.country'].search(
            [('code', '=', country_code)])

        # Search state with state_code and country id
        state_ids = self.env['res.country.state'].search([
            ('code', '=', state_code),
            ('country_id', 'in', country_ids.ids)])

        # search city with name and state
        city_ids = self.env['res.state.city'].search([
            ('name', '=', city),
            ('state_id', 'in', state_ids.ids)])

        if city_ids:
            values.update({
                'country_id': city_ids[0].state_id.country_id.id,
                'state_id': city_ids[0].state_id.id,
                'city_id': city_ids[0].id,
            })
        else:
            _logger.error(
                'Cidade retornada pela consulta de CEP não existe no sistema',
                exc_info=True)

        return self.env['br.zip'].create(values)

    @api.multi
    def get_address(self):
        """Realiza a consulta de CEP, cria uma nova entrada
        da model br.zip e retorna uma ditc contendo os valores do endereço
        recem consultado.

        Returns:
            dict -- Campos de endereço inicializados com valores do CEP.
        """
        res = {}

        # Remove pontuacao do CEP
        zip_code = re.sub('[^0-9]', '', self.zip or '')

        # Realizamos a busca pelo cep na tabela do br.zip
        br_zip = self.env['br.zip'].search([('zip', '=', zip_code)], limit=1)

        if not br_zip:
            # Realiza a consulta de CEP
            address = self.get_address_from_zip(zip_code=zip_code,
                                                environment=PRODUCAO)

            # Cria um objeto br.zip
            br_zip = self.create_br_zip_from_address(**address)

            # Converte os campo do br.zip em dicionario
            res = br_zip.convert_address_fields_to_dict()
        else:
            res = br_zip.convert_address_fields_to_dict()

        return res
