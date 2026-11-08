"""Replot the included numeric CSV examples; output is a fresh PNG, not a paper panel."""
import argparse
import csv
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib import font_manager


def plot(source, out):
    names={f.name for f in font_manager.fontManager.ttflist}
    chosen=next((f for f in ['Microsoft YaHei','Noto Sans CJK SC','SimHei','PingFang SC','WenQuanYi Zen Hei'] if f in names),None)
    if not chosen:
        raise RuntimeError('Install a Chinese font such as Noto Sans CJK SC before plotting')
    plt.rcParams.update({'font.family':chosen,'axes.unicode_minus':False,'font.size':12})
    with Path(source).open(encoding='utf-8-sig',newline='') as stream:rows=list(csv.DictReader(stream))
    output=Path(out)
    if output.exists():raise FileExistsError('Choose a new output file')
    output.parent.mkdir(parents=True,exist_ok=True)
    if 'gene' in rows[0]:
        fig,ax=plt.subplots(figsize=(8,5))
        values=[float(r['HH_div_CH']) for r in rows]
        bars=ax.barh([r['gene'] for r in rows],values,color=['#19735c','#19735c','#bf7458'])
        ax.invert_yaxis();ax.axvline(1,color='#727e77',ls='--');ax.set_xlim(0,3.1)
        ax.set_xlabel('相对表达水平（CH = 1）');ax.set_title('同样受热，三个基因的表达方向不同',loc='left',pad=20)
        ax.bar_label(bars,labels=[f'{v:g} 倍' for v in values],padding=5)
        note='HH / CH；下一代花后15天籽粒；原试验 n = 3。\n正文比值未报告独立误差，不补画误差线。DOI: 10.1038/s41598-025-99146-x'
    else:
        fig,axes=plt.subplots(1,2,figsize=(11,5),sharey=True)
        for ax,year in zip(axes,sorted({r['年份'] for r in rows})):
            group=[r for r in rows if r['年份']==year]
            values=[float(r['产量_吨每公顷']) for r in group]
            bars=ax.bar([r['前茬管理']+'\n'+r['密度'] for r in group],values,color=['#91aaa0','#91aaa0','#19735c','#19735c'])
            ax.set_title(year);ax.set_ylim(0,10)
            ax.bar_label(bars,labels=[f"{v:g}\n{r['产量统计字母']}" for v,r in zip(values,group)],padding=3)
        axes[0].set_ylabel('产量（吨/公顷）');ax=axes[-1]
        fig.suptitle('前茬管理 × 后茬密度：逐年比较产量',x=.06,ha='left')
        note='FP：常规前茬；SF：综合前茬；D1 / D2：20 / 30 穴每平方米。\n字母沿用原表同年比较；均值表未提供误差，不补画。DOI: 10.1016/j.fcr.2026.110773'
    for axis in fig.axes:
        axis.spines[['top','right']].set_visible(False)
    fig.text(.06,.02,note,fontsize=9,color='#56665e')
    fig.tight_layout(rect=(0,.16,1,.93))
    fig.savefig(output,dpi=200,facecolor='white');plt.close(fig)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('csv');p.add_argument('--out',required=True)
    a=p.parse_args();plot(a.csv,a.out)
