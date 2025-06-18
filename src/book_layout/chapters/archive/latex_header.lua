% LaTeX header to fix overfull hbox issues
\usepackage{fvextra}
\usepackage{xcolor}

% Configure code blocks to break lines
\fvset{
  breaklines=true,
  breakanywhere=true,
  breaksymbol=\color{red}\tiny\ensuremath{\hookrightarrow}
}

% Allow line breaking in URLs and similar
\usepackage{url}
\def\UrlBreaks{\do\/\do-\do.\do:}

% Reduce strictness of line breaking
\tolerance=1
\emergencystretch=\maxdimen
\hyphenpenalty=10000
\hbadness=10000

% Fix memoir head height warning
\setheadfoot{15pt}{12pt}