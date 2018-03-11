"use strict";

CodeMirror.defineMode("text/minizinc", function(config) {

  var isOperatorChar = /[+\-*=<>\/]/;

  var keywords = {"array":true,
  "bool":true,
  "case":true,
  "constraint":true,
  "diff":true,
  "div":true,
  "else":true,
  "elseif":true,
  "endif":true,
  "enum":true,
  "false":true,
  "float":true,
  "function":true,
  "if":true,
  "in":true,
  "include":true,
  "int":true,
  "intersect":true,
  "let":true,
  "list":true,
  "maximize":true,
  "minimize":true,
  "mod":true,
  "not":true,
  "of":true,
  "op":true,
  "output":true,
  "par":true,
  "predicate":true,
  "record":true,
  "satisfy":true,
  "set":true,
  "solve":true,
  "string":true,
  "subset":true,
  "superset":true,
  "symdiff":true,
  "test":true,
  "then":true,
  "true":true,
  "tuple":true,
  "type":true,
  "union":true,
  "var":true,
  "where":true,
  "xor":true};

  var punc = ":;,.(){}[]";

  function tokenBase(stream, state) {
    var ch = stream.next();
    if (ch == '"') {
      state.tokenize.push(tokenString);
      return tokenString(stream, state);
    }
    if (/[\d\.]/.test(ch)) {
      if (ch == ".") {
        stream.match(/^[0-9]+([eE][\-+]?[0-9]+)?/);
      } else if (ch == "0") {
        stream.match(/^[xX][0-9a-fA-F]+/) || stream.match(/^0[0-7]+/);
      } else {
        stream.match(/^[0-9]*\.?[0-9]*([eE][\-+]?[0-9]+)?/);
      }
      return "number";
    }
    if (ch == "/") {
      if (stream.eat("*")) {
        state.tokenize.push(tokenComment);
        return tokenComment(stream, state);
      }
    }
    if (ch == "%") {
      stream.skipToEnd();
      return "comment";
    }
    if (isOperatorChar.test(ch)) {
      stream.eatWhile(isOperatorChar);
      return "operator";
    }
    if (punc.indexOf(ch) > -1) {
      return "punctuation";
    }
    stream.eatWhile(/[\w\$_\xa1-\uffff]/);
    var cur = stream.current();
    if (keywords.propertyIsEnumerable(cur)) {
      return "keyword";
    }
    return "variable";
  }

  function tokenComment(stream, state) {
    var maybeEnd = false, ch;
    while (ch = stream.next()) {
      if (ch == "/" && maybeEnd) {
        state.tokenize.pop();
        break;
      }
      maybeEnd = (ch == "*");
    }
    return "comment";
  }

  function tokenUntilClosingParen() {
    var depth = 0;
    return function(stream, state, prev) {
      var inner = tokenBase(stream, state, prev);
      console.log("untilClosing",inner,stream.current());
      if (inner == "punctuation") {
        if (stream.current() == "(") {
          ++depth;
        } else if (stream.current() == ")") {
          if (depth == 0) {
            stream.backUp(1)
            state.tokenize.pop()
            return state.tokenize[state.tokenize.length - 1](stream, state)
          } else {
            --depth;
          }
        }
      }
      return inner;
    }
  }

  function tokenString(stream, state) {
    var escaped = false, next, end = false;
    while ((next = stream.next()) != null) {
      if (next=='(' && escaped) {
        state.tokenize.push(tokenUntilClosingParen());
        return "string";
      }
      if (next == '"' && !escaped) {end = true; break;}
      escaped = !escaped && next == "\\";
    }
    if (end || !escaped)
      state.tokenize.pop();
    return "string";
  }

  return {
    startState: function(basecolumn) {
      return {
        tokenize: []
      };
    },

    token: function(stream, state) {
      if (stream.eatSpace()) return null;
      var style = (state.tokenize[state.tokenize.length - 1] || tokenBase)(stream, state);
      console.log("token",style);
      return style;
    },

    blockCommentStart: "/*",
    blockCommentEnd: "*/",
    lineComment: "%"
  };
});

CodeMirror.defineMIME("text/minizinc", "text/minizinc");

Jupyter.CodeCell.options_default.highlight_modes['magic_text/minizinc'] = {'reg':[/^%%minizinc/]} ;

Jupyter.notebook.get_cells().map(function(cell){
  if (cell.cell_type == 'code'){ cell.auto_highlight(); }
}) ;
