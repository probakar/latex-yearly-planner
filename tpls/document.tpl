\documentclass[9pt]{extarticle}

\usepackage{geometry}
\usepackage[table]{xcolor}

\definecolor{deepolive}{HTML}{33401F}
\definecolor{mediumolive}{HTML}{7D8F52}
\definecolor{softolive}{HTML}{C7CFA3}

\colorlet{black}{deepolive}
\colorlet{gray}{mediumolive}
\colorlet{lightgray}{softolive}
{{if $.Cfg.Debug.ShowFrame}}\usepackage{showframe}{{end}}
\usepackage{calc}
\usepackage{dashrule}
\usepackage{setspace}
\usepackage{array}
\usepackage{tikz}
\usepackage{varwidth}
\usepackage{blindtext}
\usepackage{tabularx}
\usepackage{wrapfig}
\usepackage{makecell}
\usepackage{graphicx}
\usepackage{multirow}
\usepackage{amssymb}
\usepackage{expl3}
\usepackage{leading}
\usepackage{pgffor}
\usepackage{hyperref}
\usepackage{marginnote}
\usepackage{adjustbox}
\usepackage{multido}

\hypersetup{
    {{- if not .Cfg.Debug.ShowLinks}}hidelinks=true{{end -}}
}


\geometry{paperwidth={{.Cfg.Layout.Paper.Width}}, paperheight={{.Cfg.Layout.Paper.Height}}}
\geometry{
  top={{.Cfg.Layout.Paper.Margin.Top}},
  bottom={{.Cfg.Layout.Paper.Margin.Bottom}},
  left={{.Cfg.Layout.Paper.Margin.Left}},
  right={{.Cfg.Layout.Paper.Margin.Right}},
  marginparwidth={{.Cfg.Layout.Paper.MarginParWidth}},
  marginparsep={{.Cfg.Layout.Paper.MarginParSep}}
}

\pagestyle{empty}
{{if $.Cfg.Layout.Paper.ReverseMargins}}\reversemarginpar{{end}}
\newcolumntype{Y}{>{\centering\arraybackslash}X}
\parindent=0pt
\fboxsep0pt

\begin{document}
\color{black}

{{template "macro.tpl" .}}

  {{range .Pages -}}
    \include{ {{- .Name -}} }
  {{end}}
\end{document}
