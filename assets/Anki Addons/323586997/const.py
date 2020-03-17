# -*- coding: utf-8 -*-
# Copyright: (C) 2018-2020 Lovac42
# Support: https://github.com/lovac42/ReMemorize
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html


from anki import version
CCBC = version.endswith("ccbc")
ANKI21 = version.startswith("2.1.") and not CCBC

BROWSER_TAG="_reschedule" if ANKI21 else "reschedule"
