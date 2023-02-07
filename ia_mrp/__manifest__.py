# -*- coding: utf-8 -*-
{
    'name': 'I&A Manufacturing Customization',
    'version': '1.1.1',
    'summary': 'I&A Manufacturing Customization',
    'description': """  
Analytic Information in Manufacturing

    1. Odoo Gap
Out of the box, Odoo does not have the option to select or map an analytic account into a manufacturing order. 
Hence, we are looking into customizing the manufacturing application to include analytic accounts and passing 
the information on to the accounting journals.

    2. Analytic Account in MO
Introduce a new field Analytic Account in Manufacturing Order under the Miscellaneous tab.

The analytic account field will be made read-only once the manufacturing order is completed and marked as Done.

    3. Accounting Impacts
Once the MO is completed, there are 2 impacts occurring – Stock Movements and Accounting Journals. 
The Analytic Account, if selected in the MO, will be populated into the accounting journals.""",
    'author': 'Ioppolo & Associates',
    'website': 'http://www.ioppolo.com.au/',
    'support': 'odoosupport@ioppolo.com.au',
    'depends': [
        'base','stock_account','mrp','sale'
    ],
    'data': [
        'views/mrp.xml',
        'views/product_veiw.xml',
        'views/stock_quant_views.xml',
        'security/ir.model.access.csv'
    ],
    'application':True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3'
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
