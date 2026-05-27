"""
Dashboard Interactif - RFM Analysis & Customer Segmentation
Plotly Dash avec filtres interactifs
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import plotly.express as px
import mysql.connector
import pandas as pd
import os
from dotenv import load_dotenv

# Charger configuration
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', ''),
    'database': os.getenv('DB_NAME', 'ecommerce_churn')
}

# =====================================================
# CONNEXION & CHARGEMENT DONNÉES
# =====================================================

def load_data():
    """Charger données du dashboard"""
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        
        # Requête principale
        query = """
        SELECT 
            c.customer_id,
            CONCAT(c.first_name, ' ', c.last_name) as customer_name,
            c.email,
            c.city,
            c.signup_date,
            cs.rfm_score,
            cs.segment_name,
            cs.recency_days,
            cs.frequency,
            cs.monetary_value,
            cs.churn_risk,
            COALESCE((SELECT COUNT(*) FROM orders WHERE customer_id = c.customer_id), 0) as total_orders,
            COALESCE((SELECT MAX(order_date) FROM orders WHERE customer_id = c.customer_id), c.signup_date) as last_order_date
        FROM customers c
        LEFT JOIN customer_segments cs ON c.customer_id = cs.customer_id
        ORDER BY cs.rfm_score DESC
        """
        
        df = pd.read_sql(query, conn)
        conn.close()
        
        # Nettoyer les NaN (clients sans segment)
        df['rfm_score'] = df['rfm_score'].fillna(0)
        df['segment_name'] = df['segment_name'].fillna('Non calculé')
        df['churn_risk'] = df['churn_risk'].fillna('Unknown')
        
        return df
    except Exception as e:
        print(f"Erreur chargement données: {e}")
        return pd.DataFrame()

# Charger données au démarrage
df_main = load_data()

# =====================================================
# INITIALISATION DASH
# =====================================================

app = dash.Dash(__name__)
app.title = "E-Commerce Churn & RFM Dashboard"

# Couleurs
COLORS = {
    'Champion': '#27AE60',  # Vert
    'Loyal': '#3498DB',     # Bleu
    'Potential': '#F39C12',  # Orange
    'At Risk': '#E74C3C'    # Rouge
}

CHURN_COLORS = {
    'Low': '#27AE60',      # Vert
    'Medium': '#F39C12',    # Orange
    'High': '#E74C3C'      # Rouge
}

# =====================================================
# LAYOUT
# =====================================================

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🛍️ E-Commerce Churn & RFM Analysis Dashboard", style={'marginBottom': 5}),
        html.P("Segmentation clients et détection du risque de churn", style={'color': '#7F8C8D', 'marginTop': 0})
    ], style={'padding': '20px', 'backgroundColor': '#ECF0F1', 'marginBottom': '20px', 'borderRadius': '8px'}),
    
    # Filtres
    html.Div([
        html.Div([
            html.Label("🏷️ Segment:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='segment-filter',
                options=[
                    {'label': 'Tous les segments', 'value': 'all'},
                    {'label': 'Champion', 'value': 'Champion'},
                    {'label': 'Loyal', 'value': 'Loyal'},
                    {'label': 'Potential', 'value': 'Potential'},
                    {'label': 'At Risk', 'value': 'At Risk'},
                    {'label': 'Non calculé', 'value': 'Non calculé'}
                ],
                value='all',
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'marginRight': '20px'}),
        
        html.Div([
            html.Label("⚠️ Risque Churn:", style={'fontWeight': 'bold'}),
            dcc.Dropdown(
                id='churn-filter',
                options=[
                    {'label': 'Tous les risques', 'value': 'all'},
                    {'label': 'Low', 'value': 'Low'},
                    {'label': 'Medium', 'value': 'Medium'},
                    {'label': 'High', 'value': 'High'}
                ],
                value='all',
                style={'width': '100%'}
            )
        ], style={'flex': '1', 'marginRight': '20px'}),
        
        html.Div([
            html.Label("📊 Score RFM minimum:", style={'fontWeight': 'bold'}),
            dcc.Slider(
                id='score-slider',
                min=0,
                max=100,
                step=10,
                value=0,
                marks={i: str(i) for i in range(0, 101, 20)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'flex': '1.5'})
    ], style={'display': 'flex', 'padding': '20px', 'backgroundColor': '#F8F9FA', 'borderRadius': '8px', 'marginBottom': '20px', 'gap': '20px'}),
    
    # KPIs
    html.Div([
        html.Div([
            html.Div([
                html.H3("👥", style={'margin': '0', 'fontSize': '32px'}),
                html.P("Total Clients", style={'margin': '0', 'fontSize': '12px', 'color': '#7F8C8D'}),
                html.P(id='kpi-customers', style={'margin': '0', 'fontSize': '24px', 'fontWeight': 'bold'})
            ], style={'padding': '20px', 'backgroundColor': '#3498DB', 'color': 'white', 'borderRadius': '8px', 'textAlign': 'center'})
        ], style={'flex': '1'}),
        
        html.Div([
            html.Div([
                html.H3("💰", style={'margin': '0', 'fontSize': '32px'}),
                html.P("CA Moyen", style={'margin': '0', 'fontSize': '12px', 'color': '#7F8C8D'}),
                html.P(id='kpi-avg-spending', style={'margin': '0', 'fontSize': '24px', 'fontWeight': 'bold'})
            ], style={'padding': '20px', 'backgroundColor': '#27AE60', 'color': 'white', 'borderRadius': '8px', 'textAlign': 'center'})
        ], style={'flex': '1'}),
        
        html.Div([
            html.Div([
                html.H3("⚠️", style={'margin': '0', 'fontSize': '32px'}),
                html.P("% Churn High", style={'margin': '0', 'fontSize': '12px', 'color': '#7F8C8D'}),
                html.P(id='kpi-churn-high', style={'margin': '0', 'fontSize': '24px', 'fontWeight': 'bold'})
            ], style={'padding': '20px', 'backgroundColor': '#E74C3C', 'color': 'white', 'borderRadius': '8px', 'textAlign': 'center'})
        ], style={'flex': '1'}),
        
        html.Div([
            html.Div([
                html.H3("📈", style={'margin': '0', 'fontSize': '32px'}),
                html.P("Commandes Moy", style={'margin': '0', 'fontSize': '12px', 'color': '#7F8C8D'}),
                html.P(id='kpi-avg-orders', style={'margin': '0', 'fontSize': '24px', 'fontWeight': 'bold'})
            ], style={'padding': '20px', 'backgroundColor': '#F39C12', 'color': 'white', 'borderRadius': '8px', 'textAlign': 'center'})
        ], style={'flex': '1'})
    ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '30px'}),
    
    # Graphiques
    html.Div([
        html.Div([
            dcc.Graph(id='segment-pie-chart')
        ], style={'flex': '1', 'minHeight': '400px'}),
        
        html.Div([
            dcc.Graph(id='rfm-histogram')
        ], style={'flex': '1', 'minHeight': '400px'})
    ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '30px'}),
    
    # Graphiques suite
    html.Div([
        html.Div([
            dcc.Graph(id='churn-distribution')
        ], style={'flex': '1', 'minHeight': '400px'}),
        
        html.Div([
            dcc.Graph(id='recency-monetary-scatter')
        ], style={'flex': '1', 'minHeight': '400px'})
    ], style={'display': 'flex', 'gap': '20px', 'marginBottom': '30px'}),
    
    # Table
    html.Div([
        html.H3("📋 Détail des clients"),
        html.Div(id='customers-table', style={'overflowX': 'auto', 'marginTop': '20px'})
    ], style={'padding': '20px', 'backgroundColor': '#F8F9FA', 'borderRadius': '8px'})
    
], style={'padding': '20px', 'fontFamily': 'Arial, sans-serif', 'backgroundColor': '#FFFFFF'})

# =====================================================
# CALLBACKS
# =====================================================

def filter_data(segment, churn, score):
    """Filtrer données selon critères"""
    df = df_main.copy()
    
    if segment != 'all':
        df = df[df['segment_name'] == segment]
    
    if churn != 'all':
        df = df[df['churn_risk'] == churn]
    
    df = df[df['rfm_score'] >= score]
    
    return df

@callback(
    [
        Output('kpi-customers', 'children'),
        Output('kpi-avg-spending', 'children'),
        Output('kpi-churn-high', 'children'),
        Output('kpi-avg-orders', 'children'),
        Output('segment-pie-chart', 'figure'),
        Output('rfm-histogram', 'figure'),
        Output('churn-distribution', 'figure'),
        Output('recency-monetary-scatter', 'figure'),
        Output('customers-table', 'children')
    ],
    [
        Input('segment-filter', 'value'),
        Input('churn-filter', 'value'),
        Input('score-slider', 'value')
    ]
)
def update_dashboard(segment, churn, score):
    """Mettre à jour tous les graphiques"""
    
    df = filter_data(segment, churn, score)
    
    if len(df) == 0:
        # Pas de données
        return "0", "€0", "0%", "0", {}, {}, {}, {}, html.Div("Aucune donnée correspondant aux filtres")
    
    # KPIs
    kpi_customers = len(df)
    kpi_avg_spending = f"€{df['monetary_value'].mean():.2f}"
    kpi_churn_high_pct = f"{(len(df[df['churn_risk'] == 'High']) / len(df) * 100):.1f}%"
    kpi_avg_orders = f"{df['total_orders'].mean():.1f}"
    
    # Graphique 1 : Distribution Segments (Pie)
    segment_counts = df['segment_name'].value_counts()
    fig_segment = go.Figure(
        data=[go.Pie(
            labels=segment_counts.index,
            values=segment_counts.values,
            marker=dict(colors=[COLORS.get(seg, '#95A5A6') for seg in segment_counts.index]),
            hovertemplate='<b>%{label}</b><br>%{value} clients<br>%{percent}<extra></extra>'
        )],
        layout=go.Layout(
            title="📊 Distribution par Segment",
            height=400
        )
    )
    
    # Graphique 2 : Histogram RFM Score
    fig_rfm = go.Figure(
        data=[go.Histogram(
            x=df['rfm_score'],
            nbinsx=20,
            marker=dict(color='#3498DB'),
            hovertemplate='Score: %{x}<br>Nb clients: %{y}<extra></extra>'
        )],
        layout=go.Layout(
            title="📈 Distribution des Scores RFM",
            xaxis_title="RFM Score",
            yaxis_title="Nombre de clients",
            height=400,
            template='plotly_white'
        )
    )
    
    # Graphique 3 : Distribution Churn
    churn_counts = df['churn_risk'].value_counts()
    fig_churn = go.Figure(
        data=[go.Bar(
            x=churn_counts.index,
            y=churn_counts.values,
            marker=dict(color=[CHURN_COLORS.get(risk, '#95A5A6') for risk in churn_counts.index]),
            hovertemplate='%{x}<br>%{y} clients<extra></extra>'
        )],
        layout=go.Layout(
            title="⚠️ Distribution Risque Churn",
            xaxis_title="Niveau de risque",
            yaxis_title="Nombre de clients",
            height=400,
            template='plotly_white'
        )
    )
    
    # Graphique 4 : Scatter Recency vs Monetary
    fig_scatter = px.scatter(
        df,
        x='recency_days',
        y='monetary_value',
        color='segment_name',
        size='frequency',
        hover_data=['customer_name', 'total_orders'],
        color_discrete_map=COLORS,
        title="🗺️ Recency vs Monetary Value"
    )
    fig_scatter.update_layout(
        xaxis_title="Recency (jours)",
        yaxis_title="Monetary Value (€)",
        height=400,
        template='plotly_white'
    )
    
    # Table des clients
    df_table = df[[
        'customer_name', 'email', 'city',
        'rfm_score', 'segment_name', 'churn_risk',
        'recency_days', 'frequency', 'monetary_value'
    ]].head(20).copy()
    
    df_table.columns = [
        'Nom', 'Email', 'Ville',
        'Score RFM', 'Segment', 'Churn',
        'Recency (j)', 'Frequency', 'Monetary (€)'
    ]
    
    table = html.Table([
        html.Thead(
            html.Tr([html.Th(col, style={'padding': '10px', 'textAlign': 'left', 'borderBottom': '2px solid #3498DB', 'fontWeight': 'bold'}) 
                     for col in df_table.columns])
        ),
        html.Tbody([
            html.Tr([
                html.Td(
                    str(row[col])[:30],
                    style={
                        'padding': '10px',
                        'borderBottom': '1px solid #ECF0F1',
                        'backgroundColor': '#FAFAFA' if i % 2 == 0 else 'white'
                    }
                )
                for col in df_table.columns
            ], style={'hover': {'backgroundColor': '#ECF0F1'}}) 
            for i, (_, row) in enumerate(df_table.iterrows())
        ])
    ], style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '12px'})
    
    return (
        kpi_customers,
        kpi_avg_spending,
        kpi_churn_high_pct,
        kpi_avg_orders,
        fig_segment,
        fig_rfm,
        fig_churn,
        fig_scatter,
        table
    )

# =====================================================
# DÉMARRAGE
# =====================================================

if __name__ == '__main__':
    print("🚀 Démarrage du dashboard...")
    print("📊 Accéder à http://localhost:8050")
    app.run(debug=True, port=8050)
