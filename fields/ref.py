# ------------------------------------------------------------------------------
# This file is part of Appy, a framework for building applications in the Python
# language. Copyright (C) 2007 Gaetan Delannay

# Appy is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 3 of the License, or (at your option) any later
# version.

# Appy is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.

# You should have received a copy of the GNU General Public License along with
# Appy. If not, see <http://www.gnu.org/licenses/>.

# ------------------------------------------------------------------------------
import sys, re
from appy import Object
from appy.fields import Field
from appy.px import Px
from appy.gen.layout import Table
from appy.gen import utils as gutils
from appy.shared import utils as sutils

# ------------------------------------------------------------------------------
class Ref(Field):
    # Some default layouts. "w" stands for "wide": those layouts produce tables
    # of Ref objects whose width is 100%.
    wLayouts = Table('lrv-f', width='100%')
    # "d" stands for "description": a description label is added.
    wdLayouts = {'view': Table('l-d-f', width='100%')}

    # This PX displays the title of a referenced object, with a link on it to
    # reach the consult view for this object. If we are on a back reference, the
    # link allows to reach the correct page where the forward reference is
    # defined. If we are on a forward reference, the "nav" parameter is added to
    # the URL for allowing to navigate from one object to the next/previous on
    # ui/view.
    pxObjectTitle = Px('''
     <x var="includeShownInfo=includeShownInfo|False;
             navInfo='ref.%s.%s:%s.%d.%d' % (zobj.UID(), field.name, \
               field.pageName, loop.ztied.nb + 1 + startNumber, totalNumber);
             navInfo=not field.isBack and navInfo or '';
             cssClass=ztied.getCssFor('title')">
      <x>::ztied.getSupTitle(navInfo)</x>
      <a var="pageName=field.isBack and field.back.pageName or 'main';
              fullUrl=ztied.getUrl(page=pageName, nav=navInfo)"
         href=":fullUrl" class=":cssClass">:(not includeShownInfo) and \
         ztied.Title() or field.getReferenceLabel(ztied.appy())
      </a><span name="subTitle" style=":showSubTitles and 'display:inline' or \
            'display:none'">::ztied.getSubTitle()</span>
     </x>''')

    # This PX displays icons for triggering actions on a given referenced object
    # (edit, delete, etc).
    pxObjectActions = Px('''
     <table class="noStyle" var="isBack=field.isBack">
      <tr>
       <!-- Arrows for moving objects up or down -->
       <td if="not isBack and (len(zobjects)&gt;1) and changeOrder and canWrite"
          var2="objectIndex=field.getIndexOf(zobj, ztied);
                ajaxBaseCall=navBaseCall.replace('**v**','%s,%s,{%s:%s,%s:%s}'%\
                  (q(startNumber), q('doChangeOrder'), q('refObjectUid'),
                   q(ztied.UID()), q('move'), q('**v**')))">
        <img if="objectIndex &gt; 0" class="clickable" src=":url('arrowUp')"
             title=":_('move_up')"
             onclick=":ajaxBaseCall.replace('**v**', 'up')"/>
        <img if="objectIndex &lt; (totalNumber-1)" class="clickable"
             src=":url('arrowDown')" title=":_('move_down')"
             onclick=":ajaxBaseCall.replace('**v**', 'down')"/>
       </td>
       <!-- Workflow transitions -->
       <td if="ztied.showTransitions('result')"
           var2="targetObj=ztied">:targetObj.appy().pxTransitions</td>
       <!-- Edit -->
       <td if="not field.noForm and ztied.mayEdit() and field.delete">
        <a var="navInfo='ref.%s.%s:%s.%d.%d' % (zobj.UID(), field.name, \
                        field.pageName, loop.ztied.nb+startNumber, totalNumber)"
           href=":ztied.getUrl(mode='edit', page='main', nav=navInfo)">
         <img src=":url('edit')" title=":_('object_edit')"/></a>
       </td>
       <!-- Delete -->
       <td if="not isBack and field.delete and canWrite and ztied.mayDelete()">
        <img class="clickable" title=":_('object_delete')" src=":url('delete')"
             onclick=":'onDeleteObject(%s)' % q(ztied.UID())"/>
       </td>
       <!-- Unlink -->
       <td if="not isBack and field.unlink and canWrite">
        <img class="clickable" title=":_('object_unlink')" src=":url('unlink')"
             onclick=":'onUnlinkObject(%s,%s,%s)' % (q(zobj.UID()), \
                        q(field.name), q(ztied.UID()))"/>
       </td>
      </tr>
     </table>''')

    # Displays the button allowing to add a new object through a Ref field, if
    # it has been declared as addable and if multiplicities allow it.
    pxAdd = Px('''
      <input if="showPlusIcon" type="button" class="button"
        var2="navInfo='ref.%s.%s:%s.%d.%d' % (zobj.UID(), \
                field.name, field.pageName, 0, totalNumber);
              formCall='goto(%s)' % \
                q('%s/do?action=Create&amp;className=%s&amp;nav=%s' % \
                  (folder.absolute_url(), tiedClassName, navInfo));
              formCall=not field.addConfirm and formCall or \
                'askConfirm(%s,%s,%s)' % (q('script'), q(formCall), \
                                          q(addConfirmMsg));
              noFormCall=navBaseCall.replace('**v**', \
                           '%d,%s' % (startNumber, q('CreateWithoutForm')));
              noFormCall=not field.addConfirm and noFormCall or \
                'askConfirm(%s, %s, %s)' % (q('script'), q(noFormCall), \
                                            q(addConfirmMsg))"
        style=":url('buttonAdd', bg=True)" value=":_('add_ref')"
        onclick=":field.noForm and noFormCall or formCall"/>''')

    # This PX displays, in a cell header from a ref table, icons for sorting the
    # ref field according to the field that corresponds to this column.
    pxSortIcons = Px('''
     <x if="changeOrder and canWrite and ztool.isSortable(refField.name, \
            tiedClassName, 'ref')"
        var2="ajaxBaseCall=navBaseCall.replace('**v**', '%s,%s,{%s:%s,%s:%s}'% \
               (q(startNumber), q('sort'), q('sortKey'), q(refField.name), \
                q('reverse'), q('**v**')))">
      <img class="clickable" src=":url('sortAsc')"
           onclick=":ajaxBaseCall.replace('**v**', 'False')"/>
      <img class="clickable" src=":url('sortDesc')"
           onclick=":ajaxBaseCall.replace('**v**', 'True')"/>
     </x>''')

    # PX that displays referred objects as a list.
    pxViewList = Px('''<x>
     <!-- Display a simplified widget if at most 1 referenced object. -->
     <table if="atMostOneRef">
      <tr valign="top">
       <!-- If there is no object -->
       <x if="not zobjects">
        <td class="discreet">:_('no_ref')</td>
        <td>:field.pxAdd</td>
       </x>
       <!-- If there is an object -->
       <x if="zobjects">
        <td for="ztied in zobjects"
            var2="includeShownInfo=True">:field.pxObjectTitle</td>
       </x>
      </tr>
     </table>

     <!-- Display a table in all other cases -->
     <x if="not atMostOneRef">
      <div if="not innerRef or showPlusIcon" style="margin-bottom: 4px">
       (<x>:totalNumber</x>)
       <x>:field.pxAdd</x>
       <!-- The search button if field is queryable -->
       <input if="zobjects and field.queryable" type="button" class="button"
              style=":url('buttonSearch', bg=True)" value=":_('search_title')"
              onclick=":'goto(%s)' % \
                q('%s/search?className=%s&amp;ref=%s:%s' % \
                (ztool.absolute_url(), tiedClassName, zobj.UID(), \
                 field.name))"/>
      </div>

      <!-- (Top) navigation -->
      <x>:tool.pxNavigate</x>

      <!-- No object is present -->
      <p class="discreet" if="not zobjects">:_('no_ref')</p>

      <table if="zobjects" class=":innerRef and 'innerAppyTable' or ''"
             width="100%">
       <tr valign="bottom">
        <td>
         <!-- Show forward or backward reference(s) -->
         <table class=":not innerRef and 'list' or ''"
                width=":innerRef and '100%' or field.layouts['view'].width"
                var="columns=ztool.getColumnsSpecifiers(tiedClassName, \
                       field.shownInfo, dir)">
          <tr if="field.showHeaders">
           <th for="column in columns" width=":column.width"
               align="column.align" var2="refField=column.field">
            <span>:_(refField.labelId)</span>
            <x>:field.pxSortIcons</x>
            <x var="className=tiedClassName;
                    field=refField">:tool.pxShowDetails</x>
           </th>
          </tr>
          <tr for="ztied in zobjects" valign="top"
              class=":loop.ztied.odd and 'even' or 'odd'">
           <td for="column in columns"
               width=":column.width" align=":column.align"
               var2="refField=column.field">
            <!-- The "title" field -->
            <x if="refField.name == 'title'">
             <x>:field.pxObjectTitle</x>
             <div if="ztied.mayAct()">:field.pxObjectActions</div>
            </x>
            <!-- Any other field -->
            <x if="refField.name != 'title'">
             <x var="zobj=ztied; obj=ztied.appy(); layoutType='cell';
                     innerRef=True; field=refField"
                if="zobj.showField(field.name, \
                                   layoutType='result')">:field.pxRender</x>
            </x>
           </td>
          </tr>
         </table>
        </td>
       </tr>
      </table>

      <!-- (Bottom) navigation -->
      <x>:tool.pxNavigate</x>
     </x></x>''')

    # PX that displays referred objects as menus.
    pxViewMenus = Px('''
     <table><tr style="font-size: 93%">
      <td for="menu in field.getLinkedObjectsByMenu(obj, zobjects)">

       <!-- A single object in the menu: show a clickable icon to get it -->
       <a if="len(menu.zobjects)==1" var2="ztied=menu.zobjects[0]"
          class="dropdownMenu" href=":field.getMenuUrl(zobj, ztied)"
          title=":ztied.title">
        <img if="menu.icon" src=":menu.icon"/><x
             if="not menu.icon">:menu.text</x> 1</a>

       <!-- Several objects: put them in a dropdown menu -->
       <div if="len(menu.zobjects) &gt; 1" class="dropdownMenu"
            var2="dropdownId='%s_%d' % (zobj.UID(), loop.menu.nb)"
            onmouseover=":'toggleDropdown(%s)' % q(dropdownId)"
            onmouseout=":'toggleDropdown(%s,%s)' % (q(dropdownId), q('none'))">
        <img if="menu.icon" src=":menu.icon" title=":menu.text"/><x
             if="not menu.icon">:menu.text</x>
        <!-- Display the number of objects in the menu (if more than one) -->
        <x if="len(menu.zobjects) &gt; 1">:len(menu.zobjects)</x>
        <!-- The dropdown menu containing annexes -->
        <div class="dropdown" id=":dropdownId">
         <div for="ztied in menu.zobjects"
              var2="ztiedUrl=field.getMenuUrl(zobj, ztied)">
          <a href=":ztiedUrl">:ztied.title</a>
         </div>
        </div>
       </div>
      </td>
     </tr></table>''')

    # PX that displays referred objects through this field.
    pxView = Px('''
     <div var="innerRef=req.get('innerRef', False) == 'True';
               ajaxHookId=zobj.UID() + field.name;
               render=render|'list';
               startNumber=field.getStartNumber(render, req, ajaxHookId);
               info=field.getLinkedObjects(zobj, startNumber);
               zobjects=info.objects;
               totalNumber=info.totalNumber;
               batchSize=info.batchSize;
               batchNumber=len(zobjects);
               folder=zobj.getCreateFolder();
               tiedClassName=ztool.getPortalType(field.klass);
               canWrite=not field.isBack and zobj.allows(field.writePermission);
               showPlusIcon=field.mayAdd(zobj);
               atMostOneRef=(field.multiplicity[1] == 1) and \
                            (len(zobjects)&lt;=1);
               addConfirmMsg=field.addConfirm and \
                             _('%s_addConfirm' % field.labelId) or '';
               navBaseCall='askRefField(%s,%s,%s,%s,**v**)' % \
                            (q(ajaxHookId), q(zobj.absolute_url()), \
                             q(field.name), q(innerRef));
               changeOrder=field.changeOrderEnabled(zobj);
               showSubTitles=req.get('showSubTitles', 'true') == 'true'"
          id=":ajaxHookId">
      <!-- The definition of "atMostOneRef" above may sound strange: we
           shouldn't check the actual number of referenced objects. But for
           back references people often forget to specify multiplicities. So
           concretely, multiplicities (0,None) are coded as (0,1). -->

      <x if="render == 'list'">:field.pxViewList</x>
      <x if="render == 'menus'">:field.pxViewMenus</x>
     </div>''')

    # The "menus" render mode is only applicable in "cell", not in "view".
    pxCell = Px('''<x var="render=field.render">:field.pxView</x>''')

    pxEdit = Px('''
     <select if="field.link"
             var2="objects=field.getPossibleValues(obj);
                   uids=[o.UID() for o in \
                         field.getLinkedObjects(zobj).objects]"
             name=":name" id=":name" size=":isMultiple and field.height or ''"
             onchange=":field.getOnChange(zobj, layoutType)"
             multiple=":isMultiple">
      <option value="" if="not isMultiple">:_('choose_a_value')</option>
      <option for="tied in objects"
              var2="uid=tied.uid;
                    title=field.getReferenceLabel(tied, unlimited=True)"
              selected=":inRequest and (uid in requestValue) or \
                                       (uid in uids)" value=":uid"
              title=":title">:ztool.truncateValue(title, field.swidth)</option>
     </select>''')

    pxSearch = Px('''
     <!-- The "and" / "or" radio buttons -->
     <x if="field.multiplicity[1] != 1"
        var2="operName='o_%s' % name;
              orName='%s_or' % operName;
              andName='%s_and' % operName">
      <input type="radio" name=":operName" id=":orName" checked="checked"
             value="or"/>
      <label lfor=":orName">:_('search_or')</label>
      <input type="radio" name=":operName" id=":andName" value="and"/>
      <label lfor=":andName">:_('search_and')</label><br/>
     </x>
     <!-- The list of values -->
     <select var="objects=field.getPossibleValues(tool);
                  selectAll='masterValues' in req"
             name=":widgetName" size=":field.sheight" multiple="multiple"
             onchange=":field.getOnChange(ztool, 'search', className)">
      <option for="tied in objects" value=":tied.uid" selected=":selectAll"
              var2="title=field.getReferenceLabel(tied, unlimited=True)"
              title=":title">:ztool.truncateValue(title, field.swidth)</option>
     </select>''')

    def __init__(self, klass=None, attribute=None, validator=None,
                 multiplicity=(0,1), default=None, add=False, addConfirm=False,
                 delete=None, noForm=False, link=True, unlink=None, back=None,
                 show=True, page='main', group=None, layouts=None,
                 showHeaders=False, shownInfo=(), select=None, maxPerPage=30,
                 move=0, indexed=False, searchable=False,
                 specificReadPermission=False, specificWritePermission=False,
                 width=None, height=5, maxChars=None, colspan=1, master=None,
                 masterValue=None, focus=False, historized=False, mapping=None,
                 label=None, queryable=False, queryFields=None, queryNbCols=1,
                 navigable=False, changeOrder=True, sdefault='', scolspan=1,
                 swidth=None, sheight=None, sselect=None, persist=True,
                 render='list', menuIdMethod=None, menuInfoMethod=None,
                 menuUrlMethod=None):
        self.klass = klass
        self.attribute = attribute
        # May the user add new objects through this ref ?
        self.add = add
        # When the user adds a new object, must a confirmation popup be shown?
        self.addConfirm = addConfirm
        # May the user delete objects via this Ref?
        self.delete = delete
        if delete == None:
            # By default, one may delete objects via a Ref for which one can
            # add objects.
            self.delete = bool(self.add)
        # If noForm is True, when clicking to create an object through this ref,
        # the object will be created automatically, and no creation form will
        # be presented to the user.
        self.noForm = noForm
        # May the user link existing objects through this ref?
        self.link = link
        # May the user unlink existing objects?
        self.unlink = unlink
        if unlink == None:
            # By default, one may unlink objects via a Ref for which one can
            # link objects.
            self.unlink = bool(self.link)
        self.back = None
        if back:
            # It is a forward reference
            self.isBack = False
            # Initialise the backward reference
            self.back = back
            back.isBack = True
            back.back = self
            # klass may be None in the case we are defining an auto-Ref to the
            # same class as the class where this field is defined. In this case,
            # when defining the field within the class, write
            # myField = Ref(None, ...)
            # and, at the end of the class definition (name it K), write:
            # K.myField.klass = K
            # setattr(K, K.myField.back.attribute, K.myField.back)
            if klass: setattr(klass, back.attribute, back)
        # When displaying a tabular list of referenced objects, must we show
        # the table headers?
        self.showHeaders = showHeaders
        # When displaying referenced object(s), we will display its title + all
        # other fields whose names are listed in the following attribute.
        self.shownInfo = list(shownInfo)
        if not self.shownInfo: self.shownInfo.append('title')
        # If a method is defined in this field "select", it will be used to
        # return the list of possible tied objects. Be careful: this method can
        # receive, in its first argument ("self"), the tool instead of an
        # instance of the class where this field is defined. This little cheat
        # is:
        #  - not really a problem: in this method you will mainly use methods
        #    that are available on a tool as well as on any object (like
        #    "search");
        #  - necessary because in some cases we do not have an instance at our
        #    disposal, ie, when we need to compute a list of objects on a
        #    search screen.
        # NOTE that when a method is defined in field "masterValue" (see parent
        # class "Field"), it will be used instead of select (or sselect below).
        self.select = select
        # If you want to specify, for the search screen, a list of objects that
        # is different from the one produced by self.select, define an
        # alternative method in field "sselect" below.
        self.sselect = sselect or self.select
        # Maximum number of referenced objects shown at once.
        self.maxPerPage = maxPerPage
        # If param p_queryable is True, the user will be able to perform queries
        # from the UI within referenced objects.
        self.queryable = queryable
        # Here is the list of fields that will appear on the search screen.
        # If None is specified, by default we take every indexed field
        # defined on referenced objects' class.
        self.queryFields = queryFields
        # The search screen will have this number of columns
        self.queryNbCols = queryNbCols
        # Within the portlet, will referred elements appear ?
        self.navigable = navigable
        # If changeOrder is False, it even if the user has the right to modify
        # the field, it will not be possible to move objects or sort them.
        self.changeOrder = changeOrder
        # There are different ways to render a bunch of linked objects:
        # - "list" (the default) renders them as a list (=a XHTML table);
        # - "menus" renders them as a series of popup menus, grouped by type.
        # Note that render mode "menus" will only be applied in "cell" layouts.
        # Indeed, we need to keep the "list" rendering in the "view" layout
        # because the "menus" rendering is minimalist and does not allow to
        # perform all operations on Ref objects (add, move, delete, edit...).
        self.render = render
        # If render is 'menus', 2 methods must be provided.
        # "menuIdMethod" will be called, with every linked object as single arg,
        # and must return an ID that identifies the menu into which the object
        # will be inserted.
        self.menuIdMethod = menuIdMethod
        # "menuInfoMethod" will be called with every collected menu ID (from
        # calls to the previous method) to get info about this menu. This info
        # must be a tuple (text, icon):
        # - "text" is the menu name;
        # - "icon" (can be None) gives the URL of an icon, if you want to render
        #   the menu as an icon instead of a text.
        self.menuInfoMethod = menuInfoMethod
        # "menuUrlMethod" is an optional method that allows to compute an
        # alternative URL for the tied object that is shown within the menu.
        self.menuUrlMethod = menuUrlMethod
        Field.__init__(self, validator, multiplicity, default, show, page,
                       group, layouts, move, indexed, False,
                       specificReadPermission, specificWritePermission, width,
                       height, None, colspan, master, masterValue, focus,
                       historized, mapping, label, sdefault, scolspan, swidth,
                       sheight, persist)
        self.validable = self.link

    def getDefaultLayouts(self):
        return {'view': Table('l-f', width='100%'), 'edit': 'lrv-f'}

    def isShowable(self, obj, layoutType):
        res = Field.isShowable(self, obj, layoutType)
        if not res: return res
        # We add here specific Ref rules for preventing to show the field under
        # some inappropriate circumstances.
        if (layoutType == 'edit') and \
           (self.mayAdd(obj) or not self.link): return False
        if self.isBack:
            if layoutType == 'edit': return False
            else: return getattr(obj.aq_base, self.name, None)
        return res

    def getValue(self, obj, type='objects', noListIfSingleObj=False,
                 startNumber=None, someObjects=False):
        '''Returns the objects linked to p_obj through this Ref field.
           - If p_type is "objects",  it returns the Appy wrappers;
           - If p_type is "zobjects", it returns the Zope objects;
           - If p_type is "uids",     it returns UIDs of objects (= strings).

           * If p_startNumber is None, it returns all referred objects.
           * If p_startNumber is a number, it returns self.maxPerPage objects,
             starting at p_startNumber.

           If p_noListIfSingleObj is True, it returns the single reference as
           an object and not as a list.

           If p_someObjects is True, it returns an instance of SomeObjects
           instead of returning a list of references.'''
        uids = getattr(obj.aq_base, self.name, [])
        if not uids:
            # Maybe is there a default value?
            defValue = Field.getValue(self, obj)
            if defValue:
                # I must prefix call to function "type" with "__builtins__"
                # because this name was overridden by a method parameter.
                if __builtins__['type'](defValue) in sutils.sequenceTypes:
                    uids = [o.o.UID() for o in defValue]
                else:
                    uids = [defValue.o.UID()]
        # Prepare the result: an instance of SomeObjects, that will be unwrapped
        # if not required.
        res = gutils.SomeObjects()
        res.totalNumber = res.batchSize = len(uids)
        batchNeeded = startNumber != None
        if batchNeeded:
            res.batchSize = self.maxPerPage
        if startNumber != None:
            res.startNumber = startNumber
        # Get the objects given their uids
        i = res.startNumber
        while i < (res.startNumber + res.batchSize):
            if i >= res.totalNumber: break
            # Retrieve every reference in the correct format according to p_type
            if type == 'uids':
                ref = uids[i]
            else:
                ref = obj.getTool().getObject(uids[i])
                if type == 'objects':
                    ref = ref.appy()
            res.objects.append(ref)
            i += 1
        # Manage parameter p_noListIfSingleObj
        if res.objects and noListIfSingleObj:
            if self.multiplicity[1] == 1:
                res.objects = res.objects[0]
        if someObjects: return res
        return res.objects

    def getLinkedObjects(self, obj, startNumber=None):
        '''Gets the objects linked to p_obj via this Ref field. If p_startNumber
           is None, all linked objects are returned. If p_startNumber is a
           number, self.maxPerPage objects will be returned, starting at
           p_startNumber.'''
        return self.getValue(obj, type='zobjects', someObjects=True,
                             startNumber=startNumber)

    def getLinkedObjectsByMenu(self, obj, zobjects):
        '''This method groups p_zobjects into sub-lists of objects, grouped by
           menu (happens when self.render == 'menus').'''
        res = []
        # We store in "menuIds" the already encountered menus:
        # ~{s_menuId : i_indexInRes}~
        menuIds = {}
        # Browse every object from p_zobjects and put them in their menu
        # (within "res").
        for zobj in zobjects:
            menuId = self.menuIdMethod(obj, zobj.appy())
            if menuId in menuIds:
                # We have already encountered this menu.
                menuIndex = menuIds[menuId]
                res[menuIndex].zobjects.append(zobj)
            else:
                # A new menu.
                menu = Object(id=menuId, zobjects=[zobj])
                res.append(menu)
                menuIds[menuId] = len(res) - 1
        # Complete information about every menu by calling self.menuInfoMethod
        for menu in res:
            text, icon = self.menuInfoMethod(obj, menu.id)
            menu.text = text
            menu.icon = icon
        return res

    def getMenuUrl(self, zobj, ztied):
        '''We must provide the URL of the tied object p_ztied, when shown in a
           Ref field in render mode 'menus'. If self.menuUrlMethod is specified,
           use it. Else, returns the "normal" URL of the view page for the tied
           object, but without any navigation information, because in this
           render mode, tied object's order is lost and navigation is
           impossible.'''
        if self.menuUrlMethod:
            return self.menuUrlMethod(zobj.appy(), ztied.appy())
        return ztied.getUrl(nav='')

    def getStartNumber(self, render, req, ajaxHookId):
        '''This method returns the index of the first linked object that must be
           shown, or None if all linked objects must be shown at once (it
           happens when p_render is "menus").'''
        # When using 'menus' render mode, all linked objects must be shown.
        if render == 'menus': return
        # When using 'list' (=default) render mode, the index of the first
        # object to show is in the request.
        return int(req.get('%s_startNumber' % ajaxHookId, 0))

    def getFormattedValue(self, obj, value, showChanges=False):
        return value

    def getIndexType(self): return 'ListIndex'

    def getIndexValue(self, obj, forSearch=False):
        '''Value for indexing is the list of UIDs of linked objects. If
           p_forSearch is True, it will return a list of the linked objects'
           titles instead.'''
        if not forSearch:
            res = getattr(obj.aq_base, self.name, [])
            if res:
                # The index does not like persistent lists.
                res = list(res)
            else:
                # Ugly catalog: if I return an empty list, the previous value
                # is kept.
                res.append('')
            return res
        else:
            # For the global search: return linked objects' titles.
            res = [o.title for o in self.getValue(type='objects')]
            if not res: res.append('')
            return res

    def validateValue(self, obj, value):
        if not self.link: return None
        # We only check "link" Refs because in edit views, "add" Refs are
        # not visible. So if we check "add" Refs, on an "edit" view we will
        # believe that that there is no referred object even if there is.
        # If the field is a reference, we must ensure itself that multiplicities
        # are enforced.
        if not value:
            nbOfRefs = 0
        elif isinstance(value, basestring):
            nbOfRefs = 1
        else:
            nbOfRefs = len(value)
        minRef = self.multiplicity[0]
        maxRef = self.multiplicity[1]
        if maxRef == None:
            maxRef = sys.maxint
        if nbOfRefs < minRef:
            return obj.translate('min_ref_violated')
        elif nbOfRefs > maxRef:
            return obj.translate('max_ref_violated')

    def linkObject(self, obj, value, back=False):
        '''This method links p_value (which can be a list of objects) to p_obj
           through this Ref field.'''
        # p_value can be a list of objects
        if type(value) in sutils.sequenceTypes:
            for v in value: self.linkObject(obj, v, back=back)
            return
        # Gets the list of referred objects (=list of uids), or create it.
        obj = obj.o
        refs = getattr(obj.aq_base, self.name, None)
        if refs == None:
            refs = obj.getProductConfig().PersistentList()
            setattr(obj, self.name, refs)
        # Insert p_value into it.
        uid = value.o.UID()
        if uid not in refs:
            # Where must we insert the object? At the start? At the end?
            if callable(self.add):
                add = self.callMethod(obj, self.add)
            else:
                add = self.add
            if add == 'start':
                refs.insert(0, uid)
            else:
                refs.append(uid)
            # Update the back reference
            if not back: self.back.linkObject(value, obj, back=True)

    def unlinkObject(self, obj, value, back=False):
        '''This method unlinks p_value (which can be a list of objects) from
           p_obj through this Ref field.'''
        # p_value can be a list of objects
        if type(value) in sutils.sequenceTypes:
            for v in value: self.unlinkObject(obj, v, back=back)
            return
        obj = obj.o
        refs = getattr(obj.aq_base, self.name, None)
        if not refs: return
        # Unlink p_value
        uid = value.o.UID()
        if uid in refs:
            refs.remove(uid)
            # Update the back reference
            if not back: self.back.unlinkObject(value, obj, back=True)

    def store(self, obj, value):
        '''Stores on p_obj, the p_value, which can be:
           * None;
           * an object UID (=string);
           * a list of object UIDs (=list of strings). Generally, UIDs or lists
             of UIDs come from Ref fields with link:True edited through the web;
           * a Zope object;
           * a Appy object;
           * a list of Appy or Zope objects.'''
        if not self.persist: return
        # Standardize p_value into a list of Zope objects
        objects = value
        if not objects: objects = []
        if type(objects) not in sutils.sequenceTypes: objects = [objects]
        tool = obj.getTool()
        for i in range(len(objects)):
            if isinstance(objects[i], basestring):
                # We have a UID here
                objects[i] = tool.getObject(objects[i])
            else:
                # Be sure to have a Zope object
                objects[i] = objects[i].o
        uids = [o.UID() for o in objects]
        # Unlink objects that are not referred anymore
        refs = getattr(obj.aq_base, self.name, None)
        if refs:
            i = len(refs)-1
            while i >= 0:
                if refs[i] not in uids:
                    # Object having this UID must unlink p_obj
                    self.back.unlinkObject(tool.getObject(refs[i]), obj)
                i -= 1
        # Link new objects
        if objects:
            self.linkObject(obj, objects)

    def mayAdd(self, obj):
        '''May the user create a new referred object from p_obj via this Ref?'''
        # We can't (yet) do that on back references.
        if self.isBack: return gutils.No('is_back')
        # Check if this Ref is addable
        if callable(self.add):
            add = self.callMethod(obj, self.add)
        else:
            add = self.add
        if not add: return gutils.No('no_add')
        # Have we reached the maximum number of referred elements?
        if self.multiplicity[1] != None:
            refCount = len(getattr(obj, self.name, ()))
            if refCount >= self.multiplicity[1]: return gutils.No('max_reached')
        # May the user edit this Ref field?
        if not obj.allows(self.writePermission):
            return gutils.No('no_write_perm')
        # May the user create instances of the referred class?
        if not obj.getTool().userMayCreate(self.klass):
            return gutils.No('no_add_perm')
        return True

    def checkAdd(self, obj):
        '''Compute m_mayAdd above, and raise an Unauthorized exception if
           m_mayAdd returns False.'''
        may = self.mayAdd(obj)
        if not may:
            from AccessControl import Unauthorized
            raise Unauthorized("User can't write Ref field '%s' (%s)." % \
                               (self.name, may.msg))

    def changeOrderEnabled(self, obj):
        '''Is changeOrder enabled?'''
        if isinstance(self.changeOrder, bool):
            return self.changeOrder
        else:
            return self.callMethod(obj, self.changeOrder)

    def doChangeOrder(self, obj):
        '''Moves a referred object up or down.'''
        rq = obj.REQUEST
        # Move the item up (-1), down (+1) ?
        move = (rq['move'] == 'down') and 1 or -1
        # The UID of the referred object to move
        uid = rq['refObjectUid']
        uids = getattr(obj.aq_base, self.name)
        oldIndex = uids.index(uid)
        uids.remove(uid)
        newIndex = oldIndex + move
        uids.insert(newIndex, uid)

    def getPossibleValues(self, obj):
        '''This method returns the list of all objects that can be selected
           to be linked as references to p_obj via p_self. It is applicable only
           for ref fields with link=True. If master values are present in the
           request, we use field.masterValues method instead of self.select.
        '''
        req = obj.request
        if 'masterValues' in req:
            # Convert masterValue(s) from UID(s) to real object(s).
            masterValues = req['masterValues'].strip()
            if not masterValues: masterValues = None
            else:
                masterValues = masterValues.split('*')
                tool = obj.tool
                if len(masterValues) == 1:
                    masterValues = tool.getObject(masterValues[0])
                else:
                    masterValues = [tool.getObject(v) for v in masterValues]
            res = self.masterValue(obj, masterValues)
            return res
        else:
            # If this field is an ajax-updatable slave, no need to compute
            # possible values: it will be overridden by method self.masterValue
            # by a subsequent ajax request (=the "if" statement above).
            if self.masterValue and callable(self.masterValue): return []
            if not self.select:
                # No select method has been defined: we must retrieve all
                # objects of the referred type that the user is allowed to
                # access.
                return obj.search(self.klass)
            else:
                return self.select(obj)

    xhtmlToText = re.compile('<.*?>', re.S)
    def getReferenceLabel(self, refObject, unlimited=False):
        '''p_self must have link=True. I need to display, on an edit view, the
           p_refObject in the listbox that will allow the user to choose which
           object(s) to link through the Ref. The information to display may
           only be the object title or more if self.shownInfo is used.'''
        res = ''
        for fieldName in self.shownInfo:
            refType = refObject.o.getAppyType(fieldName)
            value = getattr(refObject, fieldName)
            value = refType.getFormattedValue(refObject.o, value)
            if refType.type == 'String':
                if refType.format == 2:
                    value = self.xhtmlToText.sub(' ', value)
                elif type(value) in sutils.sequenceTypes:
                    value = ', '.join(value)
            prefix = res and ' | ' or ''
            res += prefix + value
        if unlimited: return res
        maxWidth = self.width or 30
        if len(res) > maxWidth:
            res = refObject.tool.o.truncateValue(res, maxWidth)
        return res

    def getIndexOf(self, obj, refObj):
        '''Gets the position of p_refObj within this field on p_obj.'''
        uids = getattr(obj.aq_base, self.name, None)
        if not uids: raise IndexError()
        return uids.index(refObj.UID())

    def sort(self, obj):
        '''Called when the user wants to sort the content of this field.'''
        rq = obj.REQUEST
        sortKey = rq.get('sortKey')
        reverse = rq.get('reverse') == 'True'
        obj.appy().sort(self.name, sortKey=sortKey, reverse=reverse)

def autoref(klass, field):
    '''klass.field is a Ref to p_klass. This kind of auto-reference can't be
       declared in the "normal" way, like this:

       class A:
           attr1 = Ref(A)

       because at the time Python encounters the static declaration
       "attr1 = Ref(A)", class A is not completely defined yet.

       This method allows to overcome this problem. You can write such
       auto-reference like this:

       class A:
           attr1 = Ref(None)
       autoref(A, A.attr1)
    '''
    field.klass = klass
    setattr(klass, field.back.attribute, field.back)
# ------------------------------------------------------------------------------
