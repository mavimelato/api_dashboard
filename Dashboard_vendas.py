#!/usr/bin/env python
# coding: utf-8

# In[1]:


get_ipython().system('pip install dash --user')


# In[2]:


get_ipython().system('pip install dash_auth --user')


# In[3]:


import pandas as pd
from dash import Dash, html, dcc, Input, Output
import plotly.express as px
import dash_auth

# Criando o app Dash e configurando autenticação para os usuários
app = Dash(__name__)

url = "https://github.com/mavimelato/visualizacaodados/blob/main/dados.xlsx?raw=true"
df = pd.read_excel(url, engine='openpyxl')

df['Data_Pedido'] = pd.to_datetime(df['Data_Pedido'])
df['Mes'] = df['Data_Pedido'].dt.strftime('%B')

# Especificar a ordem dos meses
ordem_meses = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December']
ordem_meses.append("Todos")

# Lista de opções para filtros
lista_regional = list(df["Regional"].unique())
lista_regional.append("Todos")

lista_produtos = list(df["Nome_Produto"].unique())
lista_produtos.append("Todos")

lista_representante = list(df["Nome_Representante"].unique())
lista_representante.append("Todos")

# Agrupar os dados por mês e somar as quantidades vendidas
df_vendas_por_mes = df.groupby('Mes')['Quantidade_Vendida'].sum().reset_index()
df_vendas_por_mes['Mes'] = pd.Categorical(df_vendas_por_mes['Mes'], categories=ordem_meses, ordered=True)
df_vendas_por_mes = df_vendas_por_mes.sort_values('Mes')

df_vendas_por_regiao = df.groupby('Regional')['Quantidade_Vendida'].sum().reset_index()
df_vendas_por_regiao['Regional'] = pd.Categorical(df_vendas_por_regiao['Regional'], categories=lista_regional, ordered=True)
df_vendas_por_regiao = df_vendas_por_regiao.sort_values('Regional')

df_vendas_por_rep = df.groupby('Nome_Representante')['Quantidade_Vendida'].sum().reset_index()

# Layout do aplicativo
app.layout = html.Div([
    html.H1(children='Dashboard de Vendas', style={'textAlign': 'center'}),

    html.Div(children='''
        Análise de Dados de Vendas
    ''', style={'textAlign': 'center'}),

    html.Div([
        html.H3(children="Vendas de cada Produto", id="subtitulo"),
        dcc.Graph(id='vendas_produtos'),
        dcc.Dropdown(options=[{'label': produto, 'value': produto} for produto in lista_produtos],
                     value="Todos", id='selecao_produto', style={'width': '50%', 'margin': 'auto'}),
    ]),

    html.Div([
        html.H3(children="Total de Vendas por Região"),
        dcc.Graph(id='vendas_regiao'),
        dcc.Dropdown(options=[{'label': regiao, 'value': regiao} for regiao in lista_regional],
                     value="Todos", id='selecao_regional', style={'width': '50%', 'margin': 'auto'}),
    ]),

    html.Div([
        html.H3(children="Total de Vendas por Representante"),
        dcc.Graph(id='vendas_rep'),
        dcc.Dropdown(options=[{'label': rep, 'value': rep} for rep in lista_representante],
                     value="Todos", id='selecao_rep', style={'width': '50%', 'margin': 'auto'}),
    ]),

    html.Div([
        html.H3(children="Vendas por Estado e Cidade"),
        html.Label('Estado do Cliente'),
        dcc.Dropdown(id='estado-dropdown', options=[{'label': estado, 'value': estado} for estado in df['Estado_Cliente'].unique()], value=None),
        html.Label('Cidade do Cliente'),
        dcc.Dropdown(id='cidade-dropdown', value=None),
        dcc.Graph(id='grafico-vendas'),
    ]),

    html.Div([
        html.H3(children="Total de Vendas por Mês"),
        dcc.Graph(id='vendas_por_mes', figure=px.bar(df_vendas_por_mes, x='Mes', y='Quantidade_Vendida',
                                                      title='Quantidade Total Vendida por Mês', labels={'Quantidade_Vendida': 'Quantidade Vendida', 'Mes': 'Mês'},
                                                      template='plotly_dark', color="Mes", barmode="group")),
    ]),

    html.Div([
        html.H3(children="Total de Vendas por Região"),
        dcc.Graph(id='vendas_por_regiao', figure=px.bar(df_vendas_por_regiao, x="Regional", y="Quantidade_Vendida",
                                                         color="Regional", barmode="group")),
    ]),

    html.Div([
        html.H3(children="Total de Vendas por Representante"),
        dcc.Graph(id='vendas_por_representante', figure=px.bar(df_vendas_por_rep, x="Nome_Representante", y="Quantidade_Vendida",
                                                                color="Nome_Representante", barmode="group")),
    ]),

    html.Div([
        html.H3(children="Total de Vendas por Estado"),
        dcc.Graph(id='vendas_por_estado', figure=px.pie(df.groupby('Estado_Cliente')['Quantidade_Vendida'].sum().reset_index(),
                                                        values='Quantidade_Vendida', names='Estado_Cliente',
                                                        title='Total de Vendas por Estado')),
    ])
])

# Callback para atualizar as opções de cidades com base no estado selecionado
@app.callback(
    Output('cidade-dropdown', 'options'),
    [Input('estado-dropdown', 'value')]
)
def update_cities_options(selected_estado):
    if selected_estado is None:
        return []
    else:
        cidades_options = [{'label': cidade, 'value': cidade} for cidade in df[df['Estado_Cliente'] == selected_estado]['Cidade_Cliente'].unique()]
        return cidades_options

# Callback para atualizar o gráfico conforme o estado e a cidade selecionados
@app.callback(
    Output('grafico-vendas', 'figure'),
    [Input('estado-dropdown', 'value'),
     Input('cidade-dropdown', 'value')]
)
def update_graph(selected_estado, selected_cidade):
    if selected_estado is None or selected_cidade is None:
        return {}
    filtered_df = df[(df['Estado_Cliente'] == selected_estado) & (df['Cidade_Cliente'] == selected_cidade)]
    fig = px.bar(filtered_df, x='Nome_Produto', y='Quantidade_Vendida', title=f'Vendas em {selected_cidade}, {selected_estado}')
    return fig

# Callback para atualizar os gráficos de vendas conforme as seleções de filtros
@app.callback(
    [Output('subtitulo', 'children'),
     Output('vendas_produtos', 'figure'),
     Output('vendas_regiao', 'figure'),
     Output('vendas_rep', 'figure')],
    [Input('selecao_produto', 'value'),
     Input('selecao_regional', 'value'),
     Input('selecao_rep', 'value')]
)
def selecionar(produto, regiao, representante):
    if produto == "Todos" and regiao == "Todos" and representante == "Todos":
        texto = "Vendas de cada Produto"
        fig1 = px.bar(df_vendas_por_mes, x='Mes', y='Quantidade_Vendida',
                      title='Quantidade Total Vendida por Mês', labels={'Quantidade_Vendida': 'Quantidade Vendida', 'Mes': 'Mês'},
                      template='plotly_dark', color="Mes", barmode="group")

        fig2 = px.bar(df_vendas_por_regiao, x="Regional", y="Quantidade_Vendida", color="Regional", barmode="group")

        fig3 = px.bar(df_vendas_por_rep, x="Nome_Representante", y="Quantidade_Vendida", color="Nome_Representante", barmode="group")
    else:
        df_filtrada = df.groupby(['Nome_Produto', 'Mes'])['Quantidade_Vendida'].sum().reset_index()
        df_filtrada2 = df.groupby(['Nome_Produto', 'Regional'])['Quantidade_Vendida'].sum().reset_index()
        df_filtrada3 = df.groupby(['Nome_Produto', 'Nome_Representante'])['Quantidade_Vendida'].sum().reset_index()
        if produto != "Todos":
            df_filtrada = df_filtrada.loc[df_filtrada['Nome_Produto'] == produto, :]
        if regiao != "Todos":
            df_filtrada2 = df_filtrada2.loc[df_filtrada2["Regional"] == regiao, :]
        if representante != "Todos":
            df_filtrada3 = df_filtrada3.loc[df_filtrada3["Nome_Representante"] == representante, :]

        texto = f"Vendas do Produto de nome {produto}"
        fig1 = px.bar(df_filtrada, x='Mes', y='Quantidade_Vendida',
                      title='Quantidade Total Vendida por Mês', labels={'Quantidade_Vendida': 'Quantidade Vendida', 'Mes': 'Mês'},
                      template='plotly_dark', color="Mes", barmode="group")

        fig2 = px.bar(df_filtrada2, x="Nome_Produto", y="Quantidade_Vendida", color="Regional", barmode="group")

        fig3 = px.bar(df_filtrada3, x="Nome_Produto", y="Quantidade_Vendida", color="Nome_Produto", barmode="group", template="plotly_dark")
    return texto, fig1, fig2, fig3

# Executa o aplicativo
if __name__ == '__main__':
    app.run_server(debug=True)

