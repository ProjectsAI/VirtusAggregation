from operator import itemgetter
import matplotlib
import matplotlib.pyplot as plt
import io
import base64

from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas

from WebAppOptimizer.app.main.forms import OptimizationResultForm, GetFromLibraResultForm

matplotlib.use('Agg')

plants = ['PONTLAB_1', 'PONTLAB_2', 'PV_1', "PV_2", "WIND_1", "WIND_2", 'BESS_1', 'BESS_2', 'LOAD_1', 'LOAD_2',
          'LOAD_3', 'LOAD_4', "CONF_1", "CONF_2"]


##########################   UTILS   ##################################


def plot_results(result, resolve_method='maximized'):
    fig1, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='Time', ylabel='Active Power (kW)', title='Aggregated Flexibility')
    plt.xticks(range(0, 96, 5))

    ax.plot(result[resolve_method]['Old_f_max'], label='Flexibility Upper Bound', color='#ff7f0e')
    ax.plot(result[resolve_method]['Old_f_min'], label='Flexibility Lower Bound', color='#1f77b4')
    ax.plot(result[resolve_method]['baseline'], label='Baseline', color='#bcbd22', linewidth=1)
    plt.legend(bbox_to_anchor=(1, 1), loc=1, borderaxespad=0.3)

    fig2, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='Time', ylabel='Active Power (kW)', title='Aggregated Flexibility Optimized')
    plt.xticks(range(0, 96, 5))

    ax.plot(result[resolve_method]['F_max'], label='Optimized Flexibility UB', color='#ff7f0e')
    ax.plot(result[resolve_method]['F_min'], label='Optimized Flexibility LB', color='#1f77b4')
    ax.plot(result[resolve_method]['baseline'], label='Baseline', color='#bcbd22', linewidth=1)
    plt.legend(bbox_to_anchor=(1, 1), loc=1, borderaxespad=0.3)

    fig3, ax = plt.subplots(figsize=(8, 4))
    ax.set(xlabel='Time', ylabel='Cost (€)', title='Total Profit')
    plt.xticks(range(0, 96, 5))

    # ax.plot(result[resolve_method]['Gain_max'], label='Gain_max (' + resolve_method + ')')
    # ax.plot(result[resolve_method]['Gain_min'], label='Gain_min (' + resolve_method + ')')
    min_gain = [x * y for x, y in zip(result[resolve_method]['Gain_min'], result[resolve_method]['F_min'])]
    max_gain = [x * y for x, y in zip(result[resolve_method]['Gain_max'], result[resolve_method]['F_max'])]
    ax.plot([(x + y) / 2 for x, y in zip(min_gain, max_gain)],
            label='Mean Profit')
    plt.legend(bbox_to_anchor=(1, 1), loc=1, borderaxespad=0.3)

    # Convert plot to PNG image
    pngImage1 = io.BytesIO()
    FigureCanvas(fig1).print_png(pngImage1)
    pngImage2 = io.BytesIO()
    FigureCanvas(fig2).print_png(pngImage2)
    pngImage3 = io.BytesIO()
    FigureCanvas(fig3).print_png(pngImage3)

    # Encode PNG image to base64 string
    pngImageB64String1 = "data:image/png;base64,"
    pngImageB64String1 += base64.b64encode(pngImage1.getvalue()).decode('utf8')
    pngImageB64String2 = "data:image/png;base64,"
    pngImageB64String2 += base64.b64encode(pngImage2.getvalue()).decode('utf8')
    pngImageB64String3 = "data:image/png;base64,"
    pngImageB64String3 += base64.b64encode(pngImage3.getvalue()).decode('utf8')

    return pngImageB64String1, pngImageB64String2, pngImageB64String3


def render_get_from_libra(form, data):
    form.table_title.data = 'Date:\t' + data['date']

    for e in data['plants']:
        row = GetFromLibraResultForm()
        row.profile_id = e['id']
        row.profile_name = e['name']
        row.profile_description = e['description']
        is_ok = True
        for subel in e['subplants']:
            if subel['type'] != 'SIMPLE_STORAGE':
                is_ok *= True if subel['baseline'] is not None else False
        row.profile = '✓' if is_ok else 'X'

        form.rows.append_entry(row)


def render_data_old(data):
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


def get_selected_config(configuration, data):
    res = {'plants': []}
    for item in data:
        tmp = item
        if configuration.body[item['name']] != 0:
            tmp['quantity'] = configuration.body[item['name']]
            res['plants'].append(tmp)

    res.update({'date': str(configuration.datetime)})
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


def render_opt_result_table(form, data):
    form.table_title.data = 'Optimization for Date:\t' + data['result']['date']

    for e in data['result']['optimizations']:
        row = OptimizationResultForm()
        row.configuration = e['name']
        row.composition = e['composition']
        row.min_time = '-' if isinstance(e['minimized']['time'], str) else round(e['minimized']['time'], 2)
        row.max_time = '-' if isinstance(e['maximized']['time'], str) else round(e['maximized']['time'], 2)

        form.rows.append_entry(row)


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
