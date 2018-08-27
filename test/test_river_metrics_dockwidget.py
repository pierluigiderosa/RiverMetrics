# coding=utf-8
"""DockWidget test.

.. note:: This program is free software; you can redistribute it and/or modify
     it under the terms of the GNU General Public License as published by
     the Free Software Foundation; either version 2 of the License, or
     (at your option) any later version.

"""
from __future__ import absolute_import

__author__ = 'pierluigi.derosa@gmail.com'
__date__ = '2017-01-09'
__copyright__ = 'Copyright 2017, pierluigi de rosa'

import unittest

from qgis.PyQt.QtWidgets import QDockWidget

from river_metrics_dockwidget import RiverMetricsDockWidget

from .utilities import get_qgis_app

QGIS_APP = get_qgis_app()


class RiverMetricsDockWidgetTest(unittest.TestCase):
    """Test dockwidget works."""

    def setUp(self):
        """Runs before each test."""
        self.dockwidget = RiverMetricsDockWidget(None)

    def tearDown(self):
        """Runs after each test."""
        self.dockwidget = None

    def test_dockwidget_ok(self):
        """Test we can click OK."""
        pass

if __name__ == "__main__":
    suite = unittest.makeSuite(RiverMetricsDialogTest)
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)

