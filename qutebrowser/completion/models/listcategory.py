# vim: ft=python fileencoding=utf-8 sts=4 sw=4 et:

# Copyright 2017 Ryan Roden-Corrent (rcorre) <ryan@rcorre.net>
#
# This file is part of qutebrowser.
#
# qutebrowser is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# qutebrowser is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with qutebrowser.  If not, see <http://www.gnu.org/licenses/>.

"""Completion category that uses a list of tuples as a data source."""

import re

from PyQt5.QtCore import Qt, QSortFilterProxyModel, QModelIndex, QRegExp
from PyQt5.QtGui import QStandardItem, QStandardItemModel

from qutebrowser.utils import qtutils
from qutebrowser.commands import cmdexc


class ListCategory(QSortFilterProxyModel):

    """Expose a list of items as a category for the CompletionModel."""

    def __init__(self, name, items, delete_func=None, parent=None):
        super().__init__(parent)
        self.name = name
        self.srcmodel = QStandardItemModel(parent=self)
        self.pattern = ''
        # ListCategory filters all columns
        self.columns_to_filter = [0, 1, 2]
        self.setFilterKeyColumn(-1)
        for item in items:
            self.srcmodel.appendRow([QStandardItem(x) for x in item])
        self.setSourceModel(self.srcmodel)
        self.delete_func = delete_func

    def set_pattern(self, val):
        """Setter for pattern.

        Args:
            val: The value to set.
        """
        self.pattern = val
        val = re.sub(r' +', r' ', val)  # See #1919
        val = re.escape(val)
        val = val.replace(r'\ ', '.*')
        rx = QRegExp(val, Qt.CaseInsensitive)
        self.setFilterRegExp(rx)
        self.invalidate()
        sortcol = 0
        self.sort(sortcol)

    def lessThan(self, lindex, rindex):
        """Custom sorting implementation.

        Prefers all items which start with self.pattern. Other than that, uses
        normal Python string sorting.

        Args:
            lindex: The QModelIndex of the left item (*left* < right)
            rindex: The QModelIndex of the right item (left < *right*)

        Return:
            True if left < right, else False
        """
        qtutils.ensure_valid(lindex)
        qtutils.ensure_valid(rindex)

        left = self.srcmodel.data(lindex)
        right = self.srcmodel.data(rindex)

        leftstart = left.startswith(self.pattern)
        rightstart = right.startswith(self.pattern)

        if leftstart and rightstart:
            return left < right
        elif leftstart:
            return True
        elif rightstart:
            return False
        else:
            return left < right

    def delete_cur_item(self, index):
        """Delete the row at the given index."""
        if not self.delete_func:
            raise cmdexc.CommandError("Cannot delete this item.")
        data = [self.data(index.sibling(index.row(), i))
                for i in range(self.columnCount())]
        self.delete_func(data)
        self.removeRow(index.row(), QModelIndex())
