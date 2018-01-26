import itertools
import datetime
from collections import defaultdict, Counter

from sqlalchemy import Integer
from sqlalchemy.sql import (
        select, and_, or_, not_, cast, func, join
        )
from sqlalchemy.dialects import sqlite

from dateutil.parser import parse as date_parse

from luqum.parser import parser
from luqum.pretty import prettify
from luqum.utils import UnknownOperationResolver, LuceneTreeVisitorV2

resolver = UnknownOperationResolver()
#str(resolver(tree))

from database import (
        Item,
        FoodNutrition,
        LocalNutritionaliase,
        FoodNutritionDetails
        )
"""

HAS NUTRITION TAHINI
HAS NUTRITIONS (TAHINI, MILLET) # AND
HAS NUTRITIONS (TAHINI|MILLET) # OR
HAS NUTRITION TAHINI AND NOT NUTRITION 

LUCENE QUERIES:https://lucene.apache.org/core/2_9_4/queryparsersyntax.html
https://lucene.apache.org/solr/guide/7_2/the-standard-query-parser.html#the-standard-query-parser
https://luqum.readthedocs.io/en/latest/api.html#utilities

[] inclusive range
{} exclusive range

time:[T10 TO T13]
date:[2017-11-05 TO 2018-10-03] dates
nutrition:"TAHINI" NOT tag:"PALACINKE"
nutrition:(TAHINI AND MILLET) #has both nutritions
nutrition:(+TAHINI +MILLET) #vsebuje oboje
nutrition:TAHINI~ #Fuzzy search Tretiramo kot contains
nutrition:TAHINI? #? search for one letter _ v LIKE
nutrition:TAHINI* #* search for multiple letters % v LIKE

preberemo parse tree ugotovimo katere tabele rabimo pa generiramo sql z 
CORE sqlalchemy
http://docs.sqlalchemy.org/en/latest/core/tutorial.html#selecting
from sqlalchemy.sql import select, and_,bindparam
s = select([Item.id]).where(Item.id < bindparam('mojid'))
str(s)=
SELECT eat.id
FROM eat
WHERE eat.id < :mojid
"""

table_name_sql = {}
table_name_sql["eat"] = Item
table_name_sql["foodnutrition"] = FoodNutrition
table_name_sql["nutritionaliases"] = LocalNutritionaliase
table_name_sql["foodnutrition_details"] = FoodNutritionDetails


table_columns = {}


def get_columns(table):
    for c in table.__table__.columns:
        yield c.name

for table_name, table in table_name_sql.items():
    table_columns[table_name] = set(get_columns(table))

columns_table_raw = defaultdict(list)

for table, columns in table_columns.items():
    for column in columns:
        columns_table_raw[column].append(table)

#columns_table_raw["has_ingkey"] = ["foodnutrition_details"]

columns_table = {}
ambiguous_columns = set()

for column, tables in columns_table_raw.items():
    if len(tables) == 1:
        columns_table[column] = tables[0]
    else:
        ambiguous_columns.add(column)

print (columns_table)
print(ambiguous_columns)

class InvalidField(Exception):
    pass


def validate_field(name):
    if "." in name:
        table, column = name.split(".")
    else:
        table, column = None, name
    if table is None:
        if column in ambiguous_columns:
            raise InvalidField("FIELD {} is ambigous add table before  it".
                    format(column))
        elif column in columns_table:
            return "{}.{}".format(columns_table[column],column), \
            table_name_sql[columns_table[column]], \
            table_name_sql[columns_table[column]].__table__.columns[column]
        else:
            raise InvalidField("FIELD {} is not known column".
                    format(column))
    else:
        if table not in table_columns:
            raise InvalidField("Table {} is not known".format(table))
        current_table_columns = table_columns[table]
        if column not in current_table_columns:
            raise InvalidField("Column {} is not in {} table".format(column,
                table))
        return name, table_name_sql[table], \
    table_name_sql[table].__table__.columns[column]

class SQLTransformer(LuceneTreeVisitorV2):

    def __init__(self):
        self.fields = {}
        self.tables = set()
        self.joins = []
        self.has_ingkey_join = False
        self.having = None
        self.group_by = None
        self.where = []


    def simplify_if_same(self, children, current_node):
        """
        If two same operation are nested, then simplify
        Should be use only with should and must operations because Not(Not(x))
        can't be simplified as Not(x)
        :param children:
        :param current_node:
        :return:
        """
        for child in children:
            if type(child) is type(current_node):
                yield from self.simplify_if_same(child.children, current_node)
            else:
                yield child

    def visit_and_operation(self, *args, **kwargs):
        return self._binary_operation("AND", *args, **kwargs)
    
    def visit_or_operation(self, *args, **kwargs):
        return self._binary_operation("OR", *args, **kwargs)

    def visit_not(self, node, parents, context):
        items = [self.visit(n, parents + [node], context)
for n in self.simplify_if_same(node.children, node)]
        return not_(*items)

    def _binary_operation(self, op_type_name, node, parents, context):
        child_context = dict(context) if context is not None else {}
        if op_type_name == "AND":
            op_type = and_
        else:
            op_type = or_
        children = self.simplify_if_same(node.children, node)
        if context.get("need_in", False):
            child_context["in"] = True
        #children = node.children
        items = [self.visit(child, parents + [node], child_context) for child in
                 children]
        if context is not None and "column" in context:
            if context.get("need_in", False):
                print ("ITEMS:", items)
                if op_type_name == "AND":
                    self.having = func.count(FoodNutrition.id) == \
                        len(items)
                return op_type(context["column"].in_(items))
        return op_type(*items)

    def visit_search_field(self, node, parents, context):
        child_context = dict(context) if context is not None else {}
        if node.name.startswith("has_"):
            p_name = node.name[4:]
            self.joins.append(join(FoodNutritionDetails, LocalNutritionaliase,
                FoodNutritionDetails.ndbno==LocalNutritionaliase.ndbno))
            #self.joins.append(join(FoodNutritionDetails, FoodNutrition,
                #FoodNutritionDetails.fn_id==FoodNutrition.id))
            self.where.append(FoodNutritionDetails.fn_id==FoodNutrition.id)
            child_context["need_in"] = True
            if node.name == "has_ingkey":
                self.has_ingkey_join = True
                self.group_by = FoodNutrition.id
            #self.tables.add(FoodNutrition)
        else:
            p_name = node.name
        name, table, column = validate_field(p_name)
        self.tables.add(table)
        print ("NAME:", name, table)
        #print ("PARENTS:", type(parents[-1]))
        cur_field = self.fields.get(name, [])
        child_context["column"] = column
        enode = self.visit(node.children[0], parents + [node], child_context)
        cur_field.append(enode)
        self.fields[name] = cur_field
        return enode 

    def visit_field_group(self, node, parents, context):
        fields = self.visit(node.expr, parents + [node], context)
        print ("FIELDS:", fields)
        return fields

    def visit_word(self, node, parents, context):
        print ("W", node.value)
        if context.get("fuzzy", False):
            return context["column"].contains(node.value)
        elif "*" in node.value or "?" in node.value:
            value = node.value.replace("*", "%").replace("?", "_")
            return context["column"].like(value)

        #print ("CONTEXT:", context)
        if context.get("in", False):
            return node.value
        return context["column"] == node.value 

    def visit_range(self, node, parents, context):
        def get_val(val):
            if val == "*":
                return None
            return val
        def get_dt_val(val):
            if val is None:
                return None
            if val.upper() == "TODAY":
                return datetime.datetime.now().date()
            elif val.upper() == "NOW":
                return datetime.datetime.now()
            if len(val) <= 3:
                if val[0] == "T":
                    return int(val[1:])
                else:
                    return int(val)
            else:
                return date_parse(val, yearfirst=True)

        column = context["column"]
        column_type = context["column"].type.python_type
        low_t = None
        high_t = None
        if  column_type == datetime.datetime:
            low_t = get_dt_val(get_val(node.low.value))
            high_t = get_dt_val(get_val(node.high.value))
            #Hour only part
            if type(low_t) is int or type(high_t) is int:
                column = cast(func.strftime("%H", context["column"]),
                            Integer)
            #print ("COLUMN: DATETIME", node)
        elif column_type == int or column_type == float:
            low_t = get_val(node.low.value)
            high_t = get_val(node.high.value)
            #print ("COLUMN: INT", node)
        else:
            raise Exception("Range can only be used with Dates/integer/float "+
                    "columns not {}".format(column_type))
        if low_t is None and high_t is None:
            raise Exception("Low and High can't be both Wildcards (*)!")
        elif low_t is None:
            if node.include_high:
                return column <= high_t
            else:
                return column < high_t
        elif high_t is None:
            if node.include_low:
                return column >= low_t
            else:
                return column > low_t

        return column.between(low_t, high_t)

    def visit_phrase(self, node, parents, context):
        print ("P", node.value)
        #return node.value
        return context["column"] == node.value #.replace("*", "%").replace("?", "_")

    def visit_fuzzy(self, node, parents, context):
        child_context = dict(context) if context is not None else {}
        child_context["fuzzy"]=True
        eword = self.visit(node.term, parents + [node], child_context)
        return eword
        #return ("CONTAINS", eword)

    def get_columns(self):

        def column_filter(column):
            ignored_columns = set([
                "ash",
                "magnesium","phosphorus", "potassium",
                "sodium","zinc", "copper",
                "manganese","selenium",
                "vitaminc","thiamin",
                "riboflavin","niacin",
                "pantoacid","vitaminb6",
                "folatetotal","folateacid",
                "foodfolate","folatedfe",
                "choline","vitb12",
                "vitaiu","vitarae",
                "retinol","alphac",
                "betac","betacrypt",
                "lypocene","lutzea",
                "vite","vitk", "fasat",
                "famono","fapoly",
                "cholestrl", "density_equivalent"
                ])
            return column.name not in ignored_columns
        print ("TABLES:", self.tables)
        print ("JOINS:", [str(x) for x in self.joins])
        if len(self.tables) == 1 and len(self.joins) == 0:
            return list(self.tables)
        if len(self.tables) > 1:
            return list(filter(column_filter, itertools.chain(*(x.__table__.columns for x in
                self.tables))))
        if self.has_ingkey_join:
            return list(filter(column_filter, FoodNutrition.__table__.columns))

    def make_joins(self):
        if Item in self.tables and FoodNutrition in self.tables:
            self.joins.append(join(FoodNutrition, Item,
                    Item.calc_nutrition==FoodNutrition.id))


    def get_sql(self, query):
        print ("QUERY:", query)
        self.fields = {}
        self.tables = set()
        tree = parser.parse(query)
        rtree = resolver(tree)
        print("REPR:", repr(rtree))
        visited = (self.visit(rtree))
        print ("VISITED:", visited)
        self.make_joins()
        columns = self.get_columns()
        print ("COLUMNS:", columns)
        s = select(columns)
        for join in self.joins:
            s = s.select_from(join)
        if self.where:
            s = s.where(*self.where)
        s = s.where(visited)
        if self.having is not None:
            s = s.having(self.having)
        if self.group_by is not None:
            s = s.group_by(self.group_by)
        print (s)
        print (s.compile().params)
        return str(s.compile(compile_kwargs={"literal_binds":True},
            dialect=sqlite.dialect()))

class GraphVizitor(object):

    def __init__(self):
        self.G = pgv.AGraph(directed=True, strict=False)
        self.node_ids = Counter()

    def _get_id(self, class_name):
        cc = GraphVizitor._camel_to_lower(class_name)
        self.node_ids[cc]+=1
        return "{}{}".format(cc, self.node_ids[cc])


    @staticmethod
    def _camel_to_lower(name):
        return "".join(
                "_" + w.lower() if w.isupper() else w.lower()
                for w in name).lstrip("_")


    def visit(self, node, parents=None):
        class_name =  node.__class__.mro()[0].__name__
        label = class_name
        if "value" in vars(node):
            label+="\n"+vars(node)["value"]
        elif "name" in vars(node):
            label+="\n"+vars(node)["name"]
        elif "include_low" in vars(node):
            v = vars(node)
            if v["include_low"]:
                L="["
            else:
                L="{"
            if v["include_high"]:
                R="]"
            else:
                R="}"

            label="{}{}{}".format(L,label,R)

        id_ = self._get_id(class_name)
        #print ("IN:", type(node), id_,  node)
        self.G.add_node(id_, label=label)
        parents = parents or []
        #print ("PARENTS:", [type(x) for x in parents])
        for child in node.children:
            cid = self.visit(child, parents + [node])
            self.G.add_edge(id_, cid)
        return id_

    def graph(self, filename="graph.png"):
        #self.G.layout()
        self.G.draw(filename, prog="dot")

if __name__ == "__main__":
    import pygraphviz as pgv
    visitor = SQLTransformer()
    gv = GraphVizitor()
#tree = parser.parse('nutrition:(TAHINI MILLET) NOT tag:"PALACINKE" OR nutrition:red')
    #query = 'nutrition:(TAHINI~ MILLET) NOT description:"PALACINKE" OR nutrition:red'
    #query = ('description:palačinke~ type:HRANA')
    query = ('type:HRANA time:[T10 TO T12]')
    query = ('type:HRANA time:[2017-10-05 TO 2017-12-06]')
    query = ('kcal:[* TO 300] time:[18 TO *] time:[2017-10-05 TO *]')
    query = ('kcal:[100 TO 300] time:[TODAY TO NOW]')
    query = ('time:[2018-01-01 TO TODAY] has_ingkey:RJAVI_FIZOL_KUHAN_CESNJEVEC')
    query = ('has_ingkey:(MILLET_COOKED)')
    #query = ('has_ingkey:(TAHINI MILLET_COOKED)')
    #query = ('ingkey:TAHINI')
    #query = ('type:HRAN?')
    #query = ('kcal:[100 TO 300] time:[18 TO 21]')
    tree = parser.parse(query)
    rtree = resolver(tree)
    print("REPR:", repr(rtree))
    gv.visit(rtree)
    gv.graph("graph.png")
    print (visitor.get_sql(query))
    query = '(title:"foo bar" AND body:"quick fox") OR title:fox'
