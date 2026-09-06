#!/usr/bin/env python3
# Convertit les pages-outils Fo-le-savoir en blocs HTML autonomes, scopés .fo-tool-<key>, pour fo-grdf.fr
import re, json, os, sys
U='https://fo-grdf.fr/wp-content/uploads/2026/09/'
LOGO='https://fo-grdf.fr/wp-content/uploads/2026/09/logo-fo-energie-grdf-fc-720.png'
GH='https://fo-grdf.github.io/Fo-le-savoir/'
TOOLS={
 'tarif-agent':'saviez_vous_tarif_agent_ane_2026_fo_grdf.html',
 'grille-ieg':'synthese-modernisation-grille-ieg.html',
 'droits-familiaux':'droits_familiaux_2026_fo_grdf.html',
 'frais-deplacement':'baremes_frais_deplacement_fo_grdf.html',
 'impots-2026':'saviez_vous_impots_2026_fo_grdf.html',
 'astreinte':'astreinte_disponibilite_permanente_fo_grdf.html',
 'catalogue-epi':'guide_epi_2026_fo_grdf.html',
 'consultation-ia-resultats':'resultats_consultation_ia_dsi_fo_grdf.html',
}
FONT_RE=re.compile(r'Fraunces|DM Sans|Atkinson Hyperlegible|DM\+Sans|Atkinson\+Hyperlegible')

def split_sel(sel):
    parts=[];depth=0;cur=''
    for ch in sel:
        if ch=='(':depth+=1
        elif ch==')':depth-=1
        if ch==',' and depth==0: parts.append(cur);cur=''
        else: cur+=ch
    parts.append(cur)
    return [p.strip() for p in parts if p.strip()]

def scope_one(s,SC):
    s=re.sub(r'^html(\S*)\s+body(\S*)',lambda m:SC+m.group(1)+m.group(2),s)
    if re.match(r'^(html|body|:root)(?![\w-])',s):
        return re.sub(r'^(html|body|:root)',SC,s,count=1)
    return SC+' '+s

def find_close(css,j):
    depth=0;k=j
    while k<len(css):
        if css[k]=='{':depth+=1
        elif css[k]=='}':
            depth-=1
            if depth==0:return k
        k+=1
    return len(css)-1

def process(css,SC):
    res='';i=0
    while i<len(css):
        m=re.match(r'\s*',css[i:]);i+=m.end()
        if i>=len(css):break
        if css[i]=='@':
            j_semi=css.find(';',i);j_brace=css.find('{',i)
            if j_brace==-1 or (j_semi!=-1 and j_semi<j_brace):
                res+=css[i:j_semi+1]+'\n';i=j_semi+1;continue
            prelude=css[i:j_brace].strip();k=find_close(css,j_brace);inner=css[j_brace+1:k]
            if prelude.startswith(('@media','@supports','@container','@layer')):
                res+=prelude+'{'+process(inner,SC)+'}\n'
            else:
                res+=prelude+'{'+inner+'}\n'
            i=k+1;continue
        j=css.find('{',i)
        if j==-1:break
        sel=css[i:j].strip();k=find_close(css,j);body=css[j+1:k]
        res+=','.join(scope_one(s,SC) for s in split_sel(sel))+'{'+body+'}\n'
        i=k+1
    return res

def fix_fonts(css):
    css=re.sub(r'font-family\s*:[^;}]*',lambda m:'font-family:inherit' if FONT_RE.search(m.group(0)) or 'serif' in m.group(0) or 'sans' in m.group(0) else m.group(0),css)
    css=re.sub(r'(--[\w-]+)\s*:\s*[^;}]*',lambda m:m.group(1)+':inherit' if FONT_RE.search(m.group(0)) else m.group(0),css)
    return css

def rewrite_assets(s):
    s=s.replace('epi_images/products/${p.id}.jpg',U+'epi-${p.id}.jpg')
    s=re.sub(r"epi_images/cat-\$\{String\((c\.p|p)\)\.padStart\(2,'0'\)\}\.jpg",lambda m:U+"epi-cat-${String("+m.group(1)+").padStart(2,'0')}.jpg",s)
    s=re.sub(r'ane_images/([a-z_]+)\.jpg',lambda m:U+'ane-'+m.group(1).replace('_','-')+'.jpg',s)
    s=s.replace('img/droits/guide_rentree_scolaire_2026_couv.png',U+'guide-rentree-scolaire-2026-couv.png')
    s=s.replace('img/logo_fo.png',LOGO)
    s=re.sub(r'videos/([a-z0-9_]+)_poster\.jpg',lambda m:U+'video-'+m.group(1).replace('_','-')+'-poster.jpg',s)
    s=re.sub(r'(src|href)="videos/([^"]+)"',lambda m:m.group(1)+'="'+GH+'videos/'+m.group(2)+'"',s)
    s=re.sub(r'https://www\.destination-prevention\.fr/wp-content/uploads/2026/03/[^"\')\s]+\.png',LOGO,s)
    s=s.replace('https://www.fnem-fo.org/wp-content/uploads/2021/01/qrcode-appli.png','https://i0.wp.com/www.fnem-fo.org/wp-content/uploads/2021/01/qrcode-appli.png')
    # liens relatifs vers d'autres pages GitHub -> absolus (en attendant leur migration)
    s=re.sub(r'href="(?!https?:|mailto:|#|/|tel:)([^"]+\.html[^"]*)"',lambda m:'href="'+GH+m.group(1)+'"',s)
    return s

def build(key,fname):
    s=open(fname,encoding='utf-8',errors='ignore').read()
    SC='.fo-tool-'+key
    styles=re.findall(r'<style[^>]*>(.*?)</style>',s,re.S)
    css='\n'.join(styles)
    css=re.sub(r'/\*.*?\*/','',css,flags=re.S)
    css=fix_fonts(css)
    css=process(css,SC)
    css+=('\n{SC}{{min-height:0!important;margin:0!important;padding:0!important;background:transparent!important;color:inherit}}'
          '\n{SC} .rotate-banner,{SC} .skip-link,{SC} .a11y-toggle-bar,{SC} .a11y-toggle-wrap,{SC} .a11y-btn-wrap,{SC} footer,{SC} .footer,{SC} .foot{{display:none!important}}'
          '\n{SC} .navbar,{SC} .control-bar{{top:80px!important}}'
          '\n{SC} .page{{max-width:none;margin:0;padding:0}}'
          '\n{SC} img{{max-width:100%;height:auto}}').format(SC=SC)
    body=re.search(r'<body[^>]*>(.*)</body>',s,re.S).group(1)
    body=re.sub(r'<script[^>]*goatcounter[^>]*>\s*</script>','',body)
    body=re.sub(r'<script[^>]*gc\.zgo\.at[^>]*>\s*</script>','',body)
    body=re.sub(r'<link[^>]*fonts\.googleapis[^>]*>','',body)
    body=re.sub(r'<style[^>]*>.*?</style>','',body,flags=re.S)
    # scripts externes autorises (Chart.js cdnjs) conserves ; les autres externes retires
    ext=re.findall(r'<script[^>]*src="([^"]+)"[^>]*>\s*</script>',body)
    for e in ext:
        if 'cdnjs.cloudflare.com' not in e:
            body=re.sub(r'<script[^>]*src="'+re.escape(e)+r'"[^>]*>\s*</script>','',body)
    body=rewrite_assets(body)
    head=re.search(r'<head>(.*?)</head>',s,re.S).group(1)
    headscripts=''.join(t for t in re.findall(r'<script[^>]*src="https://cdnjs\.cloudflare\.com[^"]*"[^>]*>\s*</script>',head))
    out='<div class="fo-tool fo-tool-%s">\n%s<style>\n%s\n</style>\n%s\n</div>' % (key,headscripts+'\n' if headscripts else '',css,body.strip())
    return out, {'key':key,'src':fname,'size':len(out),'css':len(css),'ext':ext,'imgs_left':sorted(set(re.findall(r'src="((?!https?:|data:)[^"]+)"',body)))[:10],'gh_links':sorted(set(re.findall(r'href="(https://fo-grdf\.github\.io[^"]+)"',body)))}

summary=[]
for key,fname in TOOLS.items():
    out,info=build(key,fname)
    open('outils/embeds/%s.html'%key,'w',encoding='utf-8').write(out)
    summary.append(info)
json.dump(summary,open('outils/embeds/summary.json','w'),ensure_ascii=False,indent=1)
for i in summary: print(i)
