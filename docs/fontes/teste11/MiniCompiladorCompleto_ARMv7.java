import java.util.*;
import java.util.regex.*;

enum TokenType {
    NUMERO, IDENTIFICADOR, OPERADOR, PARENTESE, ATRIBUICAO
}

class Token {
    TokenType tipo;
    String lexema;

    Token(TokenType tipo, String lexema) {
        this.tipo = tipo;
        this.lexema = lexema;
    }

    public String toString() {
        return String.format("[%s: '%s']", tipo, lexema);
    }
}

class Lexer {
    private static final Pattern padrao = Pattern.compile(
        "\\s*(?:(\\d+(\\.\\d+)?)|([a-zA-Z_]\\w*)|([+\\-*/])|(=)|([()])|(#.*))");

    public static List<Token> analisar(String entrada) {
        List<Token> tokens = new ArrayList<>();
        Matcher matcher = padrao.matcher(entrada);
        while (matcher.find()) {
            if (matcher.group(1) != null) {
                tokens.add(new Token(TokenType.NUMERO, matcher.group(1)));
            } else if (matcher.group(3) != null) {
                tokens.add(new Token(TokenType.IDENTIFICADOR, matcher.group(3)));
            } else if (matcher.group(4) != null) {
                tokens.add(new Token(TokenType.OPERADOR, matcher.group(4)));
            } else if (matcher.group(5) != null) {
                tokens.add(new Token(TokenType.ATRIBUICAO, matcher.group(5)));
            } else if (matcher.group(6) != null) {
                tokens.add(new Token(TokenType.PARENTESE, matcher.group(6)));
            }
        }
        return tokens;
    }
}

class ASTNode {
    String valor;
    ASTNode esquerda, direita;

    ASTNode(String valor) {
        this.valor = valor;
    }
}

public class MiniCompiladorCompleto_ARMv7 {

    static int tempCount = 1;
    static int regCount = 0;

    static List<String> tokens;
    static int pos = 0;

    static Map<String, String> tabelaSimbolos = new HashMap<>();

    public static void main(String[] args) {
        Scanner sc = new Scanner(System.in);
        System.out.print("Digite uma expressão infixada: ");
        String entrada = sc.nextLine();

        List<Token> tokensLexicos = Lexer.analisar(entrada);
        System.out.println("\n🔍 Tokens gerados pelo analisador léxico:");
        tokensLexicos.forEach(System.out::println);

        tokens = new ArrayList<>();
        for (Token t : tokensLexicos) {
            tokens.add(t.lexema);
        }

        pos = 0;
        ASTNode raiz = parseExpr();

        System.out.println("\n🌳 Árvore Sintática Abstrata (AST):");
        imprimirAST(raiz, 0);

        System.out.println("\n📦 Código de Três Endereços (TAC):");
        gerarTAC(raiz);

        System.out.println("\n⚙️ Assembly ARMv7 (CPUlator):");
        System.out.println(".global _start\n.text\n_start:");
        gerarAssemblyARM(raiz);
        System.out.println("    b .    @ loop infinito para parar o programa");

        System.out.println("\n📚 Tabela de Símbolos:");
        tabelaSimbolos.forEach((k, v) -> System.out.printf("🔹 %s → %s%n", k, v));

        System.out.println("\n🧮 Resultado final da expressão:");
        double resultado = avaliarExpressao(raiz);
        System.out.println("➡️  " + resultado);
    }

    static ASTNode parseExpr() {
        ASTNode node = parseTerm();
        while (pos < tokens.size() && (tokens.get(pos).equals("+") || tokens.get(pos).equals("-"))) {
            String op = tokens.get(pos++);
            ASTNode direita = parseTerm();
            ASTNode pai = new ASTNode(op);
            pai.esquerda = node;
            pai.direita = direita;
            node = pai;
        }
        return node;
    }

    static ASTNode parseTerm() {
        ASTNode node = parseFactor();
        while (pos < tokens.size() && (tokens.get(pos).equals("*") || tokens.get(pos).equals("/"))) {
            String op = tokens.get(pos++);
            ASTNode direita = parseFactor();
            ASTNode pai = new ASTNode(op);
            pai.esquerda = node;
            pai.direita = direita;
            node = pai;
        }
        return node;
    }

    static ASTNode parseFactor() {
        String token = tokens.get(pos++);
        if ("(".equals(token)) {
            ASTNode node = parseExpr();
            pos++; // consome ")"
            return node;
        } else {
            registrarSimbolo(token);
            return new ASTNode(token);
        }
    }

    static void registrarSimbolo(String token) {
        if (!isOperador(token) && !tabelaSimbolos.containsKey(token)) {
            if (token.matches("\\d+(\\.\\d+)?")) {
                tabelaSimbolos.put(token, "CONST");
            } else {
                tabelaSimbolos.put(token, "VAR");
            }
        }
    }

    static void imprimirAST(ASTNode node, int nivel) {
        if (node == null) return;
        imprimirAST(node.direita, nivel + 1);
        System.out.println("  ".repeat(nivel) + node.valor);
        imprimirAST(node.esquerda, nivel + 1);
    }

    static String gerarTAC(ASTNode node) {
        if (!isOperador(node.valor)) return node.valor;
        String a1 = gerarTAC(node.esquerda);
        String a2 = gerarTAC(node.direita);
        String temp = "t" + tempCount++;
        System.out.printf("%s = %s %s %s%n", temp, a1, node.valor, a2);
        return temp;
    }

    static String gerarAssemblyARM(ASTNode node) {
        if (!isOperador(node.valor)) {
            String reg = "r" + regCount++;
            System.out.printf("    MOV    %s, #%s%n", reg, node.valor);
            return reg;
        }

        String a1 = gerarAssemblyARM(node.esquerda);
        String a2 = gerarAssemblyARM(node.direita);
        String reg = "r" + regCount++;

        String instr = switch (node.valor) {
            case "+" -> "ADD";
            case "-" -> "SUB";
            case "*" -> "MUL";
            case "/" -> "DIV_UNSUPPORTED";
            default  -> "NOP";
        };

        if (instr.equals("DIV_UNSUPPORTED")) {
            System.out.printf("    @ divisão não suportada: %s / %s    @ resultado de '%s'%n", a1, a2, formatExpr(node));
        } else {
            System.out.printf("    %-6s %s, %s, %s    @ resultado de '%s'%n", instr, reg, a1, a2, formatExpr(node));
        }

        return reg;
    }

    static double avaliarExpressao(ASTNode node) {
        if (!isOperador(node.valor)) {
            if (node.valor.matches("\\d+(\\.\\d+)?")) {
                return Double.parseDouble(node.valor);
            } else {
                System.err.println("⚠️ Variável '" + node.valor + "' não tem valor atribuído. Usando 0.");
                return 0;
            }
        }
        double esq = avaliarExpressao(node.esquerda);
        double dir = avaliarExpressao(node.direita);
        return switch (node.valor) {
            case "+" -> esq + dir;
            case "-" -> esq - dir;
            case "*" -> esq * dir;
            case "/" -> dir != 0 ? esq / dir : Double.NaN;
            default  -> 0;
        };
    }

    static boolean isOperador(String s) {
        return "+-*/".contains(s);
    }

    static String formatExpr(ASTNode node) {
        if (node == null) return "";
        if (!isOperador(node.valor)) return node.valor;
        return "(" + formatExpr(node.esquerda) + " " + node.valor + " " + formatExpr(node.direita) + ")";
    }
}
