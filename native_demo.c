#include <stdio.h>
#include <stdlib.h>

int add(int a, int b) {
    return (a + b);
}

int factorial(int n) {
    if ((n <= 1)) {
        return 1;
    }
    return (n * factorial((n - 1)));
}

int main() {
    int x = 10;
    int y = 20;
    int sum = add(x, y);
    printf("%d\n", sum);
    printf("%d\n", factorial(5));
    return 0;
}
