#!/usr/bin/env python 
'''
Copyright (C) 2013 Terry Brown, terry_n_brown@yahoo.com

Aligns boxes with text in Inkscape - see .inx file.

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 2 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
'''

import os
import subprocess
import sys
import tempfile

from math import sqrt, pow

try:
    import inkex
except ImportError:
    sys.path.append('/usr/share/inkscape/extensions')
    import inkex

class TextBox(inkex.Effect):
    def __init__(self):
        inkex.Effect.__init__(self)
        opts = [
            ('', '--left', 'string', 'left', '20', 'Left padding px'),
            ('', '--right', 'string', 'right', '20', 'Right padding px'),
            ('', '--top', 'string', 'top', '20', 'Top padding px'),
            ('', '--bottom', 'string', 'bottom', '24', 'Bottom padding px'),
        ]
        for o in opts:
            self.OptionParser.add_option(o[0], o[1], action="store", type=o[2],
                                         dest=o[3], default=o[4], help=o[5])

    def effect(self):

        # save file and run another inkscape instance on it with --query_all
        # to get id,x,y,width,height data for all objects in file        
        temp_fh, temp_path = tempfile.mkstemp()
        os.close(temp_fh)
        self.document.write(temp_path)
        dims = subprocess.Popen(
            ("inkscape --without-gui --query-all "+temp_path).split(),
            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        dims, err = dims.communicate()
        dims = [i.split(',') for i in dims.split('\n')]
        dims = dict((str(i[0]), [float(j) for j in i[1:]]) for i in dims)
        os.unlink(temp_path)
        # dims is now a dict of x,y,width,height with id for keys

        # get centers of boxes
        box_center = {}
        for k in self.selected:
            ele = self.selected[k]
            if not k or ele.tag.endswith('text') or ele.tag.endswith('flowRoot'):
                continue
            box_center[k] = (
                dims[k][0] + dims[k][2] / 2,
                dims[k][1] + dims[k][3] / 2
            )
                        
        # get padding as floats (eval strings to allow ("720 - 90 / 4" etc.)
        left, right, top, bottom = [
            eval(i) for i in [self.options.left, self.options.right, 
                              self.options.top, self.options.bottom]
        ]
                              
        # size boxes for text
        for k in self.selected:
            ele = self.selected[k]
            if not (ele.tag.endswith('text') or ele.tag.endswith('flowRoot')):
                continue
            text_center = (
                dims[k][0] + dims[k][2] / 2,
                dims[k][1] + dims[k][3] / 2
            )
            
            # make list of all center to center distances, items are (dist, id)
            dists = [( sqrt( pow(text_center[0]-box_center[i][0], 2) +
                             pow(text_center[1]-box_center[i][1], 2)), i)
                     for i in box_center]
            # sort shortest first
            dists.sort(key=lambda x: x[0])
            # use shortest distance, arbitrary in case of ties
            box_id = dists[0][1]
            box = self.selected[box_id] 
            text_id = k    

            box.set('x', str(dims[text_id][0] - left))
            box.set('y', str(dims[text_id][1] - top))
            box.set('width', str(dims[text_id][2] + left + right))
            box.set('height', str(dims[text_id][3] + top + bottom))
        
e = TextBox()
e.affect()
