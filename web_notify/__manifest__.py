# pylint: disable=missing-docstring
# Copyright 2016 ACSONE SA/NV
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Web Notify',
    'version': '17.0',
    'sequence': 1,
    'summary': 'Web Notify',
    'website': 'https://ript.vn',
    'category': 'Uncategorized',
    'description': """Web Notify""",
    'author': "RIPT",
    "depends": ["web", "bus", "base", "mail"],
    "assets": {
        "web.assets_backend": [
            "web_notify/static/src/js/services/*.js",
        ]
    },
    "demo": ["views/res_users_demo.xml"],
    "installable": True,
}
