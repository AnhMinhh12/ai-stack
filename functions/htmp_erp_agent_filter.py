"""
title: ERP agent staging profile
author: HTMP Platform
version: 0.1.0
required_open_webui_version: 0.6.0
"""


class Filter:
    async def inlet(self, body, __model__=None):
        if ((__model__ or {}).get('id') or body.get('model')) != 'htmp-erp-agent-staging':
            return body
        # Match the existing ERP filter's explicit attachment for regular chats.
        # Do not mix the old unrestricted SQL planner into this profile.
        body['tool_ids'] = ['htmp_erp_agent']
        body.pop('files', None)
        body.setdefault('metadata', {}).pop('files', None)
        return body
