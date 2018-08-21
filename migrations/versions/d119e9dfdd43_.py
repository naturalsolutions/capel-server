"""empty message

Revision ID: d119e9dfdd43
Revises: d1463f8b68d2
Create Date: 2018-08-20 10:58:03.601136

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd119e9dfdd43'
down_revision = 'd1463f8b68d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('offenses',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('start_at', sa.DateTime(), nullable=True),
    sa.Column('end_at', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.Unicode(length=255), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    #op.drop_table('hello_zozo')
    #op.drop_table('us_lex')
    #op.drop_table('us_rules')
    #op.drop_table('spatial_ref_sys')
    #op.drop_table('ama')
    #op.drop_table('coeurs')
    #op.drop_table('sites')
    #op.drop_table('us_gaz')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('us_gaz',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('seq', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('word', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('stdword', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('token', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_custom', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='pk_us_gaz')
    )
    op.create_table('sites',
    sa.Column('id', sa.BIGINT(), autoincrement=False, nullable=False),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='MULTIPOINT', srid=4326), autoincrement=False, nullable=True),
    sa.Column('source', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('nom_site_p', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('lat', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('long', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('numerisati', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('precision', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('ssm', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('reg_dept', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('classe_m', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('type_site', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('dispo_amar', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('expo_vents', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('site_abrit', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('freq_nb_pl', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('interet_pl', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('habitats_p', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('etat_conse', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('perim_prot', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('struct_ges', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('conflits_u', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('sensib', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('prof_min', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('prof_max', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('naturel', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('artificiel', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('encadre', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('acces_libr', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('nivminreq', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('actconcern', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mesenplace', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('etatconser', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('criteco', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('pressplong', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('pressautus', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('critusages', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('valpaysag', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('connaiseco', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('connaisusa', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('critconnai', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('critgest', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('nivenjeux', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('enjeux', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('indiceprio', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.Column('priorite', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('interpgest', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('interpconn', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('interpusag', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('categorie', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('refdocgest', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('refpublisc', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('refquest', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('refbddlign', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('refcoorgps', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('date', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('id_site', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('interet', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='sites_pkey')
    )
    op.create_table('coeurs',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326), autoincrement=False, nullable=True),
    sa.Column('objectid', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('amp_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('mpa_name', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_orinam', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('des_id', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('des_desigf', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('des_desigt', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_status', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_stat_1', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('desmpa_des', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_wdpaid', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('mpa_wdpapi', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_mnhnid', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_marine', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('mpa_calcar', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('mpa_calcma', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('mpa_repare', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('mpa_repmar', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.Column('mpa_foruma', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('mpa_url', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('mpa_update', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('mpa_dateen', sa.DATE(), autoincrement=False, nullable=True),
    sa.Column('iucn_idiuc', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('subloc_cod', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('subloc_nam', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('country_pi', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('country_is', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('country__1', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='coeurs_pkey')
    )
    op.create_table('ama',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326), autoincrement=False, nullable=True),
    sa.Column('"id"', sa.BIGINT(), autoincrement=False, nullable=True),
    sa.Column('classe', sa.VARCHAR(length=35), autoincrement=False, nullable=True),
    sa.Column('secteur', sa.VARCHAR(length=25), autoincrement=False, nullable=True),
    sa.Column('secteur0', sa.VARCHAR(length=30), autoincrement=False, nullable=True),
    sa.Column('s-classe', sa.VARCHAR(length=35), autoincrement=False, nullable=True),
    sa.Column('descript', sa.VARCHAR(length=254), autoincrement=False, nullable=True),
    sa.Column('surf_ha', sa.NUMERIC(), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='ama_pkey')
    )
    op.create_table('spatial_ref_sys',
    sa.Column('srid', sa.INTEGER(), autoincrement=False, nullable=False),
    sa.Column('auth_name', sa.VARCHAR(length=256), autoincrement=False, nullable=True),
    sa.Column('auth_srid', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('srtext', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.Column('proj4text', sa.VARCHAR(length=2048), autoincrement=False, nullable=True),
    sa.CheckConstraint('(srid > 0) AND (srid <= 998999)', name='spatial_ref_sys_srid_check'),
    sa.PrimaryKeyConstraint('srid', name='spatial_ref_sys_pkey')
    )
    op.create_table('us_rules',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('rule', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('is_custom', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='pk_us_rules')
    )
    op.create_table('us_lex',
    sa.Column('id', sa.INTEGER(), nullable=False),
    sa.Column('seq', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('word', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('stdword', sa.TEXT(), autoincrement=False, nullable=True),
    sa.Column('token', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('is_custom', sa.BOOLEAN(), server_default=sa.text('true'), autoincrement=False, nullable=False),
    sa.PrimaryKeyConstraint('id', name='pk_us_lex')
    )
    op.create_table('hello_zozo',
    sa.Column('id', sa.VARCHAR(), autoincrement=False, nullable=False),
    sa.Column('geom', geoalchemy2.types.Geometry(geometry_type='MULTIPOLYGON', srid=4326), autoincrement=False, nullable=True),
    sa.Column('"id"', sa.INTEGER(), autoincrement=False, nullable=True),
    sa.Column('classe', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('secteur', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('secteur0', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('s-classe', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('descript', sa.VARCHAR(), autoincrement=False, nullable=True),
    sa.Column('surf_ha', postgresql.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True),
    sa.PrimaryKeyConstraint('id', name='hello_zozo_pkey')
    )
    op.drop_table('offenses')
    # ### end Alembic commands ###
