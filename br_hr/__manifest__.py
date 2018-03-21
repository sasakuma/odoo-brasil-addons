# © 2014 KMEE (http://www.kmee.com.br)
# @author Luis Felipe Mileo <mileo@kmee.com.br>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

{
    'name': 'Brazilian Localization HR',
    'description': """Brazilian Localization HR with informations
        refered to the national context of HR""",
    'category': 'Localization',
    'author': 'KMEE',
    'license': 'AGPL-3',
    'sequence': 45,
    'maintainer': 'MultidadosTI',
    'website': 'http://www.multidadosti.com.br/',
    'version': '11.0.1.0.0',
    'depends': [
        'hr',
        'br_base',
    ],
    'data': [
        'data/br_hr.cbo.csv',
        'security/ir.model.access.csv',
        'view/br_hr_cbo.xml',
        'view/hr_employee.xml',
        'view/hr_job.xml',
    ],
    'post_init_hook': 'post_init',
    'installable': True,
    'auto_install': False,
    'application': False,
}
