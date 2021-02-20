from collections import namedtuple
from operator import itemgetter
import matplotlib
import matplotlib.pyplot as plt
import io
import base64

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from tabulate import tabulate

matplotlib.use('Agg')

plants = ['PONTLAB_1', 'PONTLAB_2', 'PV_1', "PV_2", "WIND_1", "WIND_2", 'BESS_1', 'BESS_2', 'LOAD_1', 'LOAD_2',
          'LOAD_3', 'LOAD_4', "CONF_1", "CONF_2"]


##########################   UTILS   ##################################
def get_selected_config(configuration, data):
    res = {'plants': []}
    for item in data:
        tmp = item
        if configuration.body[item['name']] != 0:
            tmp['quantity'] = configuration.body[item['name']]
            res['plants'].append(tmp)

    res.update({'date': str(configuration.datetime)})
    return res


def render_data(data):
    res = 'Date: ' + data['date'] + '\n\n'

    for element in data['plants']:
        res += 'ID: {}\n' \
               'Name: {}\n'.format(element['id'], element['name'])
        if element['type'] == 'MIX':
            res += 'Mixed Configuration composed by:\n'
        for sub_element in element['subplants']:
            res += '\tID: {}\n' \
                   '\tName: {}\n' \
                   '\tBaseline: {}\n'.format(sub_element['id'], sub_element['name'], sub_element['baseline'])
        res += '\n\n'

    return res


def format_matrix(header, matrix,
                  top_format, left_format, cell_format, row_delim, col_delim):
    table = [[''] + header] + [[name] + row for name, row in zip(header, matrix)]
    table_format = [['{:^{}}'] + len(header) * [top_format]] \
                   + len(matrix) * [[left_format] + len(header) * [cell_format]]
    col_widths = [max(
        len(format.format(cell, 0))
        for format, cell in zip(col_format, col))
        for col_format, col in zip(zip(*table_format), zip(*table))]
    return row_delim.join(
        col_delim.join(
            format.format(cell, width)
            for format, cell, width in zip(row_format, row, col_widths))
        for row_format, row in zip(table_format, table))


def extract_max_col_width(elements):
    name_w = 0
    comp_w = 0
    for e in elements:
        name_w = len(e['name']) if len(e['name']) > name_w else name_w
        comp_w = len(e['composition']) if len(e['composition']) > comp_w else comp_w

    return name_w, comp_w


def render_opt_result(data):
    res = 'Optimization for Date:\t' + data['result']['date'] + '\n\n'

    name_w, comp_w = extract_max_col_width(data['result']['optimizations'])
    print(name_w)
    print(comp_w)

    res += tabulate([[e['name'], e['composition'],
                      '-' if isinstance(e['minimized']['time'], str) else round(e['minimized']['time'], 2),
                      '-' if isinstance(e['maximized']['time'], str) else round(e['maximized']['time'], 2)] for e in
                     data['result']['optimizations']],
                    headers=['Configuration', 'Composition', 'Time for minimizazion(s)', 'Time for maximization(s)'],
                    tablefmt='simple')

    return res


def search_by_name(name, dictlist):
    return [element for element in dictlist if element['name'] == name]


def create_profiles(data):
    result = {'plants': [],
              'date': data['date']
              }
    for element in data['data']:
        for i in range(1, int(element['quantity']) + 1):
            tmp = element.copy()
            tmp['id'] = str(tmp['id']) + '-' + str(i)
            tmp['name'] = str(tmp['name']) + '-' + str(i)
            tmp.pop('quantity')
            result['plants'].append(tmp)
    return result


def create_profiles_from_config_old(uvam, configuration):
    result = {}
    for key in configuration:
        if key != 'date':
            element = search_by_name(key, uvam['plants'])
            for i in range(1, int(configuration[key]) + 1):
                el = {key + '-' + str(i): element}
                result.update(el)

    result.update({'date': configuration['date']})
    return result


def subdict(d, ks):
    vals = []
    if len(ks) >= 1:
        vals = itemgetter(*ks)(d)
        if len(ks) == 1:
            vals = [vals]
    return dict(zip(ks, vals))


def plot_results(result, resolve_method='maximized'):
    fig, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='Time', ylabel='Active Power (kW)', title='Aggregated Flexibility Results')
    plt.xticks(range(0, 96, 5))
    ax.plot(result[resolve_method]['MIN_GRID'], label='MIN_Flex ('+resolve_method+')')
    ax.plot(result[resolve_method]['MAX_GRID'], label='MAX_Flex ('+resolve_method+')')
    #ax.plot(result[resolve_method]['RES'], label='RES (maximized)')
    # plt.legend(bbox_to_anchor=(1, 1), loc=1, borderaxespad=0.3)
    plt.legend(bbox_to_anchor=(1, 1), loc='best', borderaxespad=0.)

    fig2, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='Time', ylabel='Cost (€/kW)', title='Costs')
    plt.xticks(range(0, 96, 5))
    ax.plot(result[resolve_method]['GAIN'], label='GAIN ('+resolve_method+')')
    # plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.legend(bbox_to_anchor=(1, 1), loc='best', borderaxespad=0.)

    fig3, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='Time', ylabel='', title='BUY/SELL Activity')
    plt.xticks(range(0, 96, 5))
    ax.plot(result[resolve_method]['SELLING'], label='SELLING ('+resolve_method+')')
    ax.plot(result[resolve_method]['BUYING'], label='BUYING ('+resolve_method+')')
    # plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    plt.legend(bbox_to_anchor=(1, 1), loc='best', borderaxespad=0.)

    # Convert plot to PNG image
    pngImage = io.BytesIO()
    FigureCanvas(fig).print_png(pngImage)
    pngImage2 = io.BytesIO()
    FigureCanvas(fig2).print_png(pngImage2)
    pngImage3 = io.BytesIO()
    FigureCanvas(fig3).print_png(pngImage3)

    # Encode PNG image to base64 string
    pngImageB64String = "data:image/png;base64,"
    pngImageB64String += base64.b64encode(pngImage.getvalue()).decode('utf8')
    pngImageB64String2 = "data:image/png;base64,"
    pngImageB64String2 += base64.b64encode(pngImage2.getvalue()).decode('utf8')
    pngImageB64String3 = "data:image/png;base64,"
    pngImageB64String3 += base64.b64encode(pngImage3.getvalue()).decode('utf8')

    return pngImageB64String, pngImageB64String2, pngImageB64String3
