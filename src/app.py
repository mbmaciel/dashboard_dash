import locale
import dash
from dash import dcc, html, Input, Output #, Patch
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import mysql.connector
from datetime import date, datetime
from dateutil.relativedelta import relativedelta
import dash_bootstrap_components as dbc
import dash_ag_grid as dag
from dash_bootstrap_templates import ThemeSwitchAIO #, load_figure_template
# import plotly.io as pio



# ========== STYLES ============ #
# Definindo temas

# load_figure_template(["minty", "minty_dark"])

template_theme1 = "flatly"
template_theme2 = "vapor"
url_theme1 = dbc.themes.FLATLY
url_theme2 = dbc.themes.VAPOR


# Criando estilizações
header_card = {
    'background': 'linear-gradient(90deg, #22c1c3 0%, #2161ab 100%)',
    'height': '70px'
}

tab_card_indicators = {
    'margin': {'t':0, 'b':0},
    'text-align': 'center',
    'display': 'flex',
    'align-items': 'center',
    'justify-content': 'center',
    # 'background': 'linear-gradient(to right, #ff7e5f, #feb47b)',
    'background': 'linear-gradient(90deg, #22c1c3 0%, #2161ab 100%)',
    'border': '1px solid #00CC96',
    'border-radius': '5px'
}

tab_cardbody = {
    'padding': '5px',
    'height': '100%',
    'width': '100%',
    'display': 'flex',
    'align-items': 'center',
    'justify-content': 'center',
    'border': '2px solid #00CC96',
    'border-radius': '5px'
}

table_cardbody = {
    'padding': '5px',
    'height': '450px',
    'width': '100%',
    'border': '2px solid #00CC96',
    'border-radius': '5px'
}

main_config = {
    "hovermode": "x unified",
    "margin": {"l":0, "r":0, "t":0, "b":0},
    "paper_bgcolor": "rgba(0, 0, 0, 0)"
}

main_config_cards = {
    "margin": {"l":0, "r":0, "t":40, "b":0},
    "paper_bgcolor": "rgba(0, 0, 0, 0)",
    "plot_bgcolor": "rgba(0, 0, 0, 0)",
    "font_color": "#FFFFFF",
    "height": 120
}

# ========== SETTINGS ============ #
# Defina a localização para o Brasil
#locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

#Definir Datas
dtFim = date.today()
dtIni = dtFim - relativedelta(months=3, days=dtFim.day-1)

dti = date(dtFim.year, dtFim.month, 1)
dtf_ant = dtFim - relativedelta(months=1)
dti_ant = datetime(dtf_ant.year, dtf_ant.month, 1)


# ========== CONNECTION ============ #
# Conectar-se ao banco de dados MySQL
conn = mysql.connector.connect(
    host='srv1199.hstgr.io',
    user='u456013314_sistemanitrous',
    password='Consultoria#1',
    database='u456013314_sistemanitro',
    connect_timeout=120)

# Consulta SQL para obter dados
df_cli = pd.read_sql('SELECT id as idCliente,cliente FROM cliente;', conn)
df_mc = pd.read_sql(f'SELECT idMovimentoCaixa,cast(dataContabil as datetime) as dataContabil,cast(hora as int) as hora,vlDesconto,vlTotalReceber,vlTotalRecebido,vlServicoRecebido,vlTrocoDinheiro,vlTrocoRepique,vlTaxaEntrega,numPessoas,operacaoId,cancelado,idCliente FROM movimentocaixa_ncrcolibri WHERE dataContabil BETWEEN "{dtIni}" AND "{dtFim}";', conn)
df_mp = pd.read_sql('SELECT idMovimentoCaixa,nome as formaPgto,valor,idCliente FROM meiospagamento_movimentocaixa_ncrcolibri;', conn)
df_sc = pd.read_sql('SELECT idMovimentoCaixa,status FROM statuscomprovante_movimentocaixa_ncrcolibri;', conn)
df_iv = pd.read_sql(f'SELECT cast(dtLancamento as datetime) as dataContabil, cast(horaLancamento as int) as hora, grupoNome, descricao as item, cast(valorUnitario as float) as valorUnitario, cast(quantidade as int) as quantidade, cast(valorTotal as float) as valorTotal, operacaoId, idCliente FROM itemvenda_ncrcolibri WHERE dtLancamento BETWEEN "{dtIni}" AND "{dtFim}";', conn)

# Fechar a conexão com o banco de dados
conn.close()


# ========== CLEANING DATA ============ #
# Mesclar tabelas de movimento
df_merged = df_mc.merge(df_mp, on=["idMovimentoCaixa","idCliente"]).merge(df_sc, on="idMovimentoCaixa").merge(df_cli, on="idCliente").drop(columns=["vlDesconto","vlTotalReceber","vlTotalRecebido","vlServicoRecebido","vlTrocoDinheiro","vlTrocoRepique","vlTaxaEntrega","numPessoas"])

# Criar Colunas Necessárias
dias = {"0": "Domingo", "1": "Segunda-feira", "2": "Terça-Feira", "3": "Quarta-Feira", "4": "Quinta-Feira", "5": "Sexta-Feira", "6": "Sábado"}
df_merged['DiaSemana'] = df_merged["dataContabil"].apply(lambda x: x.strftime('%w')).replace(dias)
df_merged["Semana"] = "S " + df_merged["dataContabil"].apply(lambda x: x.strftime('%U'))
df_merged["pgto"] = "Outros"
df_merged.loc[df_merged["formaPgto"].str.contains('cred|CRED|créd|CRÉD|Cred|Créd') == True, "pgto"] = "Crédito"
df_merged.loc[df_merged["formaPgto"].str.contains('deb|DEB|déb|DÉB|Déb|Deb') == True, "pgto"] = "Débito"
df_merged.loc[df_merged["formaPgto"].str.contains('vouc|VOUC|Vouc') == True, "pgto"] = "Voucher"
df_merged.loc[df_merged["formaPgto"].str.contains('pix|PIX|Pix') == True, "pgto"] = "Pix"
df_merged.loc[df_merged["formaPgto"].str.contains('foo|FOO') == True, "pgto"] = "Ifood"
df_merged.loc[df_merged["formaPgto"].str.contains('Din|din|DIN') == True, "pgto"] = "Dinheiro"

# Definir DFs que serão utilizados
df_cancelados = df_merged[df_merged["status"] == "Cancelado"]
df_movimento = df_merged[df_merged["status"] != "Cancelado"]
df_item = df_iv

# To dict - para salvar no dcc.store
df_canc = df_cancelados.to_dict()
df_mov = df_movimento.to_dict()
df_it = df_item.to_dict()


app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, dbc.icons.FONT_AWESOME])

# Declare server for Heroku deployment. Needed for Procfile.
server = app.server

# ========== LAYOUT ============ #
app.layout = dbc.Container(children=[
    # Armazenamento de dataset
    dcc.Store(id='dataset_mov', data=df_mov),
    dcc.Store(id='dataset_canc', data=df_canc),
    dcc.Store(id='dataset_item', data=df_it),
 
    #ROW 1 - Name, Theme and Date Picker
    dbc.Navbar(
        dbc.Container([
            dbc.Col([
                dbc.Row([    
                    dbc.Col([
                        html.Legend('EMPRESA XYZ', style={'color': 'white'}),
                    ], lg=7),
                    dbc.Col([
                        # dbc.Label(className="fa fa-moon", html_for="switch"),
                        # dbc.Switch( id="switch", value=False, className="d-inline-block ms-1", persistence=True),
                        # dbc.Label(className="fa fa-sun", html_for="switch"),
                       ThemeSwitchAIO(aio_id="theme", themes=[url_theme1, url_theme2])
                    ], lg=5)
                ], align='center')
            ], lg=4),
            dbc.Col([
                html.Label('Selecione o Período:',
                            style={'color': 'white', 'margin-left':'10px', 'margin-right':'10px'}),
                dcc.DatePickerRange(
                            id='date-picker-first-period',
                            display_format='DD/MM/YYYY',
                            start_date=dti,
                            end_date=dtFim,
                            updatemode='bothdates',
                            style={'border': '1px solid #00CC96'})
            ], lg=8, style={'text-align': 'right'}),
        ], fluid=True), 
    style=header_card, className='fixed-top'),           

    # ROW 2 - Cards
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='card-faturamento-bruto',
                            config={"displayModeBar": False, "showTips": False})
            ], style=tab_card_indicators)
        ], lg=2, style={'margin-left': '0px', 'margin-right': '-5px'}),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='card-ticket-medio',
                            config={"displayModeBar": False, "showTips": False})
            ], style=tab_card_indicators)
        ], lg=2, style={'margin-left': '-5px', 'margin-right': '-5px'}),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='card-fiscal',
                            config={"displayModeBar": False, "showTips": False})
            ], style=tab_card_indicators)
        ], lg=2, style={'margin-left': '-5px', 'margin-right': '-5px'}),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='card-talonario',
                            config={"displayModeBar": False, "showTips": False})
            ], style=tab_card_indicators)
        ], lg=2, style={'margin-left': '-5px', 'margin-right': '-5px'}),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='card-vendas-totais',
                            config={"displayModeBar": False, "showTips": False})
            ], style=tab_card_indicators)
        ], lg=2, style={'margin-left': '-5px', 'margin-right': '-5px'}),
        dbc.Col([
            dbc.Card([
                dcc.Graph(id='card-cancelados',
                            config={"displayModeBar": False, "showTips": False})
            ], style=tab_card_indicators)
        ], lg=2, style={'margin-left': '-5px', 'margin-right': '0px'})                                        
    ], justify='between', className='main_row g-2 my-auto'),

    # ROW 3 - Gráficos de faturamento por dia e Curva ABC 
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        id='heatmap',
                        config={"displayModeBar": False, "showTips": False}
                    ),
                    dcc.Graph(
                        id='curva-abc',
                        config={"displayModeBar": False, "showTips": False}
                    ),         
                   
                ], style=tab_cardbody)
            ], style={'height':'370px'})
        ], lg=12)

    ], className='main_row g-2 my-auto'),
    
    # ROW 4 - Gráficos de faturamento por semana, dia da semana e forma de pagamento,
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                   dbc.Row([
                        dbc.Col([

                            dcc.Graph(
                                id='grafico-vendas-dia-semana',
                                config={"displayModeBar": False, "showTips": False}
                            )  
                        ], lg=6),
                        dbc.Col([
                            dcc.Graph(
                                id='grafico-vendas-semana',
                                config={"displayModeBar": False, "showTips": False}
                            ),
                        ], lg=6)
                    ])
                    
                ], style=tab_cardbody)
            ], style={'height':'260px'})
        ], lg=6),
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            dcc.Graph(
                                id='grafico-formapgto',
                                config={"displayModeBar": False, "showTips": False}
                            ),
                        ], lg=6),
                        dbc.Col([
                            dcc.Graph(
                                id='grafico-formapgto-pizza',
                                config={"displayModeBar": False, "showTips": False}
                            )
                        ], lg=6),
                    ])           
                ], style=tab_cardbody)
            ], style={'height':'260px'})
        ], lg=6)
    ], className='main_row g-2 my-auto'),
        
   # ROW 5 - Tabela Ranking de Itens Vendidos
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("Ranking Itens"),
                    dag.AgGrid(
                        id='tabela-rank',
                        columnDefs=[
                            {'headerName': 'Grupo', 'field': 'grupoNome', 'sortable': True, 'filter': True},
                            {'headerName': 'Item', 'field': 'item', 'sortable': True, 'filter': True},
                            {'headerName': 'Valor Total', 'field': 'valorTotal', 'sortable': True, 'filter': True, 'type': 'numericColumn','cellDataType': 'number'},
                            {'headerName': 'Quantidade', 'field': 'quantidade', 'sortable': True, 'filter': True, 'type': 'numericColumn','cellDataType': 'number'},
                        ],
                        columnSize="sizeToFit",
                    )
                ], style=table_cardbody)
            ])
        ], lg=12),
    ], className='main_row g-2 my-auto')

], fluid=True, style={'height': '100%',
                      'margin-top': '70px',
                      'margin-bottom':'20px',
                      'overflow-x': 'hidden'})

@app.callback(
    [
    Output('card-faturamento-bruto', 'figure'),
    Output('card-ticket-medio', 'figure'),
    Output('card-fiscal', 'figure'),
    Output('card-talonario', 'figure'),
    Output('card-vendas-totais', 'figure'),
    Output('card-cancelados', 'figure')
    ],
    [
    Input('dataset_mov', 'data'),
    Input('dataset_canc', 'data'),
    Input('date-picker-first-period', 'start_date'),
    Input('date-picker-first-period', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def cards(data, canc, start_date_first, end_date_first, toggle):
    template = template_theme1 if toggle else template_theme2

    df_movimento = pd.DataFrame(data)
    df_cancelados = pd.DataFrame(canc)

    # Filtrando Dataframes
    df_movimento = df_movimento[(df_movimento['dataContabil'] >= start_date_first) & (df_movimento['dataContabil'] <= end_date_first)]
    df_emitido = df_movimento[df_movimento['status'] == 'Emitido']
    df_nao_emitido = df_movimento[df_movimento['status'] != 'Emitido']
    df_cancelados = df_cancelados[(df_cancelados['dataContabil'] >= start_date_first) & (df_cancelados['dataContabil'] <= end_date_first)]

    # Criando Strings
    faturamento_bruto = df_movimento['valor'].sum()
    vendas_totais = (df_movimento["operacaoId"]).nunique()
    ticket_medio = faturamento_bruto / vendas_totais
    fiscal = df_emitido['valor'].sum()
    nao_fiscal = df_nao_emitido['valor'].sum()
    cancelados = df_cancelados['operacaoId'].nunique()


    # Formatando as datas para o formato BRL
    # start_date_first_str = datetime.fromisoformat(start_date_first.split('T')[0]).strftime('%d/%m/%Y')
    # end_date_first_str = datetime.fromisoformat(end_date_first.split('T')[0]).strftime('%d/%m/%Y')
  
    # Criando os Cards
    card1 = go.Figure()
    card1.add_trace(go.Indicator(
        mode = "number+delta",
        title = {"text": f"<span style='font-size:18px'>Faturamento Bruto</span>"},
        value = faturamento_bruto,
        number = {'valueformat': ',.0f'},
        number_font={"size": 34}))
        # delta = {'relative': True, 'valueformat': '.1%', 'reference': faturamento_segundo_periodo}))
    card1.update_layout(main_config_cards, template=template)

    card2 = go.Figure()
    card2.add_trace(go.Indicator(
        mode = "number+delta",
        title = {"text": f"<span style='font-size:18px'>Ticket Médio</span>"},
        value = ticket_medio,
        number = {'valueformat': ',.2f'},
        number_font={"size": 34}))
        # delta = {'relative': True, 'valueformat': '.1%', 'reference': ticket_segundo_periodo}))
    card2.update_layout(main_config_cards, template=template)

    card3 = go.Figure()
    card3.add_trace(go.Indicator(
        mode = "number+delta",
        title = {"text": f"<span style='font-size:18px'>Fiscal</span>"},
        value = fiscal,
        number = {'valueformat': ',.0f'},
        number_font={"size": 34}))
        # delta = {'relative': True, 'valueformat': '.1%', 'reference': fiscal_segundo_periodo}))
    card3.update_layout(main_config_cards, template=template)

    card4 = go.Figure()
    card4.add_trace(go.Indicator(
        mode = "number+delta",
        title = {"text": f"<span style='font-size:18px'>Talonário</span>"},
        value = nao_fiscal,
        number = {'valueformat': ',.0f'},
        number_font={"size": 34}))
    card4.update_layout(main_config_cards, template=template)

    card5 = go.Figure()
    card5.add_trace(go.Indicator(
        mode = "number+delta",
        title = {"text": f"<span style='font-size:18px'>Vendas</span>"},
        value = vendas_totais,
        number = {'valueformat': ',.0f'},
        number_font={"size": 34}))
    card5.update_layout(main_config_cards, template=template)

    card6 = go.Figure()
    card6.add_trace(go.Indicator(
        mode = "number+delta",
        title = {"text": f"<span style='font-size:18px'>Cancelados</span>"},
        value = cancelados,
        number = {'valueformat': ',.0f'},
        number_font={"size": 34}))
    card6.update_layout(main_config_cards, template=template)


    fig = [card1, card2, card3, card4, card5, card6]

    return fig
  
@app.callback(
    [
    Output('heatmap', 'figure')
    ],
    [
    Input('dataset_mov', 'data'),
    Input('date-picker-first-period', 'start_date'),
    Input('date-picker-first-period', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def heatmap(data, start_date_first, end_date_first, toggle):
    template = template_theme1 if toggle else template_theme2

    df_movimento = pd.DataFrame(data)

    # Filtrando Dataframes
    df_movimento = df_movimento[(df_movimento['dataContabil'] >= start_date_first) & (df_movimento['dataContabil'] <= end_date_first)].sort_values(by='dataContabil', ascending=True)

    # Agrupando os dados
    heatmap = df_movimento.groupby(['Semana', 'DiaSemana']).agg({'valor': 'sum'}).reset_index()
    heatmap['DiaSemana'] = pd.Categorical(heatmap['DiaSemana'],
                                                          categories=['Domingo','Segunda-feira', 'Terça-Feira', 'Quarta-Feira', 'Quinta-Feira', 'Sexta-Feira', 'Sábado'],
                                                          ordered=True)
    
    heatmap_colorscale = [[0, 'rgba(0, 0, 0, 0)'],
                          [0.0000001, 'rgba(255, 0, 0, 1)'],
                          [0.5, 'rgba(255, 255, 0, 1)'],
                          [1, 'rgba(0, 255, 0, 1)']]
 
    # Heatmap Faturamento por dia
    grafico_heatmap = px.imshow(heatmap.pivot_table(index='Semana', columns='DiaSemana', values='valor', fill_value=0),
                                         labels=dict(x="Dia da Semana", y="Semana", color="Faturamento"),
                                         x=['Dom','Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb'],
                                         y=df_movimento['Semana'].unique(),
                                         title='Faturamento por Dia',
                                         text_auto=',.0f',                                         
                                         color_continuous_scale=heatmap_colorscale)
    grafico_heatmap.update_layout(xaxis_title='',
                                        yaxis_title='',
                                        margin=dict(l=0, t=40, r=20, b=10),
                                        height=350,
                                        plot_bgcolor='rgba(0,0,0,0)',
                                        paper_bgcolor='rgba(0, 0, 0, 0)',
                                        xaxis=dict(showgrid=False, side='top'),
                                        yaxis=dict(showgrid=False),
                                        coloraxis_showscale=False, 
                                        template=template)
 
    
    fig = [grafico_heatmap]

    return fig

@app.callback(
    [
     Output('curva-abc', 'figure')
    ],
    [
    Input('dataset_item', 'data'),
    Input('date-picker-first-period', 'start_date'),
    Input('date-picker-first-period', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def curva_abc(data, start_date_first, end_date_first, toggle):
    template = template_theme1 if toggle else template_theme2

    df_item = pd.DataFrame(data)

    # Filtrando Dataframes
    df_item = df_item[(df_item['dataContabil'] >= start_date_first) & (df_item['dataContabil'] <= end_date_first)]
 
    # Criar tabela de curva ABC
    df_abc = df_item.groupby('grupoNome')['valorTotal'].sum().reset_index().sort_values(by='valorTotal', ascending=False)
    df_abc['percentual_acumulado'] = df_abc['valorTotal'].cumsum() / df_abc['valorTotal'].sum() * 100
    
    # Configuração do gráfico
    grafico_abc = make_subplots(specs=[[{"secondary_y": True}]])

    # Adicionar a curva ABC como uma linha
    grafico_abc.add_trace(go.Scatter(
                                            x=df_abc['grupoNome'].head(20),
                                            y=df_abc['percentual_acumulado'],
                                            mode='lines',
                                            name='Curva ABC'),
                                            secondary_y=True
    )

    # Adicionar barras para representar os somatórios por categoria
    grafico_abc.add_trace(go.Bar(
                                            x=df_abc['grupoNome'].head(20),
                                            y=df_abc['valorTotal'],
                                            name='Faturamento',
                                            hovertemplate='%{y:,.2f}'),
                                            secondary_y=False
    )

    grafico_abc.update_layout(
                                    title='Curva ABC',
                                    xaxis_title='',
                                    yaxis_title='',
                                    height=350,
                                    plot_bgcolor='rgba(0,0,0,0)',
                                    paper_bgcolor='rgba(0, 0, 0, 0)',
                                    margin=dict(l=0,t=40,b=0,r=0), 
                                    yaxis=dict(showgrid=False),
                                    showlegend=False,
                                    hovermode='x unified', 
                                    template=template
    )
    grafico_abc.update_traces(hovertemplate='%{y:.2f}%',
                                               selector=dict(type='scatter'))

  
    fig = [grafico_abc]

    return fig

@app.callback(
    [
    Output('grafico-vendas-dia-semana', 'figure'),
    Output('grafico-vendas-semana', 'figure')
    ],
    [
    Input('dataset_mov', 'data'),
    Input('date-picker-first-period', 'start_date'),
    Input('date-picker-first-period', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def semana(data, start_date_first, end_date_first, toggle):
    template = template_theme1 if toggle else template_theme2

    df_movimento = pd.DataFrame(data)

    # Filtrando Dataframes
    df_movimento = df_movimento[(df_movimento['dataContabil'] >= start_date_first) & (df_movimento['dataContabil'] <= end_date_first)]
  
    faturamento_diadasemana = df_movimento.groupby(['DiaSemana'], as_index=False)['valor'].sum()
    faturamento_semana = df_movimento.groupby(by=["Semana"], as_index=False)["valor"].sum().sort_values(by="Semana", ascending=False)
   
    #Grafico barras Faturamento Semanal
    grafico_semana = px.bar(faturamento_semana,
                                            y = "Semana",
                                            x = "valor",
                                            title='Faturamento por Semana',
                                            orientation="h",
                                            labels={"Semana": "Semana", "valor": "Faturamento"},
                                            text=["{:,.1f}k".format(x) for x in faturamento_semana["valor"] / 1000],
                                            height = 250)
    grafico_semana.update_layout(xaxis_title='',
                                                yaxis_title='',
                                                margin=dict(l=0,t=40,b=0,r=10),                                                
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                paper_bgcolor='rgba(0,0,0,0)',
                                                xaxis=dict(showgrid=False),
                                                yaxis=dict(showgrid=False), 
                                                template=template)
    grafico_semana.update_traces(showlegend=False,marker_color="cyan")
    grafico_semana.update_xaxes(showticklabels=False)

    # Gráfico Pizza Vendas por dia da Semana
    gráfico_diasemana = px.pie(faturamento_diadasemana,
                                                values='valor',
                                                names='DiaSemana',
                                                title='Faturamento por Dia da Semana',
                                                labels={'valor': 'Faturamento'},
                                                hover_data=['valor'],
                                                color_discrete_sequence=["#1CFFCE", "#FE00CA", "#2ED9FF", "#F6F926", "#16FF32", "#00CC96", "#FF6692"],
                                                height = 230,
                                                hole=0.3)
    gráfico_diasemana.update_layout(yaxis_tickformat=',.0f',
                                                    margin=dict(l=10,t=40,b=0,r=10),
                                                    paper_bgcolor='rgba(0,0,0,0)', 
                                                    template=template)
    gráfico_diasemana.update_traces(textposition='inside',
                                                    text=["{:,.0f}".format(x) for x in faturamento_diadasemana["valor"]],
                                                    textinfo='label+text+percent',
                                                    hovertemplate='%{label}: %{value:,.0f}',
                                                    showlegend=False)

    
    fig = [grafico_semana, gráfico_diasemana]

    return fig

@app.callback(
    [
    Output('grafico-formapgto', 'figure'),
    Output('grafico-formapgto-pizza', 'figure')
    ],
    [
    Input('dataset_mov', 'data'),
    Input('date-picker-first-period', 'start_date'),
    Input('date-picker-first-period', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def formapgto(data, start_date_first, end_date_first, toggle):
    template = template_theme1 if toggle else template_theme2

    df_movimento = pd.DataFrame(data)

    # Filtrando Dataframes
    df_movimento = df_movimento[(df_movimento['dataContabil'] >= start_date_first) & (df_movimento['dataContabil'] <= end_date_first)]
    
    # Agrupando os dados
    formapgto = df_movimento.groupby(['pgto'], as_index=False)['valor'].sum().sort_values(by="valor", ascending=True)

    # Grafico de Faturamento por Forma de Pgto
    grafico_formapgto = px.bar(formapgto,
                                            y = "pgto",
                                            x = "valor",
                                            title='Faturamento por Forma Pgto',
                                            orientation="h",
                                            labels={"pgto": "Forma Pgto", "valor": "Faturamento"},
                                            text=["{:,.1f}k".format(x) for x in formapgto["valor"] / 1000],
                                            height = 250)
    grafico_formapgto.update_layout(xaxis_title='',
                                                yaxis_title='',
                                                margin=dict(l=0,t=40,b=0,r=10),
                                                paper_bgcolor='rgba(0,0,0,0)',                                               
                                                plot_bgcolor='rgba(0,0,0,0)',
                                                xaxis=dict(showgrid=False),
                                                yaxis=dict(showgrid=False), 
                                                template=template)
    grafico_formapgto.update_traces(showlegend=False,marker_color="magenta")
    grafico_formapgto.update_xaxes(showticklabels=False)

   # Gráfico Pizza Vendas por Forma de Pgto
    grafico_formapgto_pizza = px.pie(formapgto,
                                                values='valor',
                                                names='pgto',
                                                title='Faturamento por Forma de Pgto',
                                                labels={'valor': 'Faturamento'},
                                                hover_data=['valor'],
                                                color_discrete_sequence=["#1CFFCE", "#FE00CA", "#2ED9FF", "#F6F926", "#16FF32", "#00CC96", "#FF6692"],
                                                height = 230,
                                                hole=0.3)
    grafico_formapgto_pizza.update_layout(yaxis_tickformat=',.0f',
                                                    margin=dict(l=10,t=40,b=0,r=10),
                                                    paper_bgcolor='rgba(0,0,0,0)', 
                                                    template=template)
    grafico_formapgto_pizza.update_traces(textposition='inside',
                                                    text=["{:,.0f}".format(x) for x in formapgto["valor"]],
                                                    textinfo='label+text+percent',
                                                    hovertemplate='%{label}: %{value:,.0f}',
                                                    showlegend=False)

  
    fig = [grafico_formapgto,
           grafico_formapgto_pizza]

    return fig

@app.callback(
    [
     Output('tabela-rank', 'rowData')
    ],
    [
    Input('dataset_item', 'data'),
    Input('date-picker-first-period', 'start_date'),
    Input('date-picker-first-period', 'end_date'),
    Input(ThemeSwitchAIO.ids.switch("theme"), "value")
    ]
)
def ranking_item(data, start_date_first, end_date_first, toggle):
    template = template_theme1 if toggle else template_theme2

    df_item = pd.DataFrame(data)

    # Filtrando Dataframes
    df_item = df_item[(df_item['dataContabil'] >= start_date_first) & (df_item['dataContabil'] <= end_date_first)]

    # Calcular o ranking por item e ordenar por valorTotal
    ranking = df_item.groupby(by=['grupoNome','item'])[['valorTotal','quantidade']].sum().reset_index().sort_values(by='valorTotal', ascending=False)
    
    # Formatar dados para as tabelas
    data = ranking.to_dict('records')

    return [data]


# @app.callback(
#     Output("graph", "figure"),
#     Input("switch", "value"),
# )
# def update_figure_template(switch_on):
#     # When using Patch() to update the figure template, you must use the figure template dict
#     # from plotly.io  and not just the template name
#     template = pio.templates["minty"] if switch_on else pio.templates["minty_dark"]

#     patched_figure = Patch()
#     patched_figure["layout"]["template"] = template
#     return patched_figure



# Execute o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)
