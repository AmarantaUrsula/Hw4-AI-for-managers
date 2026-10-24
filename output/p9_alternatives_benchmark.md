# Problem 9 — find_alternatives benchmark

Same model (gpt-6-luna via Portkey), same prompt except the sold-out rule, same 3 questions.

| Question | Agent | Model requests | Tokens | Seconds | Tool calls | Cards |
|---|---|---|---|---|---|---|
| Do you have this in a large? If not, what else could I get in L? (fencing-left-chest-hoodie) | WITH find_alternatives | 2 | 8783 | 4.1 | get_stock, find_alternatives | 3 |
| Do you have this in a large? If not, what else could I get in L? (fencing-left-chest-hoodie) | WITHOUT (search + get_stock) | 3 | 12065 | 5.6 | get_stock, search_products | 3 |
| I need a small in this. Anything similar if it's gone? (davenport-college-crewneck) | WITH find_alternatives | 2 | 8773 | 4.1 | get_stock, find_alternatives | 3 |
| I need a small in this. Anything similar if it's gone? (davenport-college-crewneck) | WITHOUT (search + get_stock) | 4 | 16559 | 7.7 | get_stock, search_products, search_products | 6 |
| Is this available in XL? Otherwise show me something like it. (champion-reverse-weave-hoodie-1) | WITH find_alternatives | 3 | 12663 | 5.4 | get_stock, find_alternatives | 3 |
| Is this available in XL? Otherwise show me something like it. (champion-reverse-weave-hoodie-1) | WITHOUT (search + get_stock) | 5 | 21854 | 6.9 | get_stock, get_product_description, search_products, get_stock | 2 |

**Totals**

| Agent | Model requests | Tokens | Seconds |
|---|---|---|---|
| WITH find_alternatives | 7 | 30219 | 13.6 |
| WITHOUT (search + get_stock) | 12 | 50478 | 20.1 |

**Replies**

- *WITH find_alternatives* — Do you have this in a large? If not, what else could I get in L?: Size L is sold out in the Fencing Left Chest Hoodie. Similar hoodies available in L are the Crew Left Chest Hoodie (8 in stock), Squash Left Chest Hoodie (25 in stock), and Volleyball Left Chest Hoodie (8 in stock).
- *WITHOUT (search + get_stock)* — Do you have this in a large? If not, what else could I get in L?: Size L is sold out in the Fencing Left Chest Hoodie. You could try another item in L—there are 78 matches, including the Basic Hoodie Big Yale, Baseball Left Chest Crewneck, and Benjamin Franklin 1/4 Zip. The full set is on the page; the hoodie is also available in S, M, and XL.
- *WITH find_alternatives* — I need a small in this. Anything similar if it's gone?: Size S is sold out in the Davenport College Crewneck. Similar styles available in S include the Jonathan Edwards College Crewneck (25 in stock), Pierson College Crewneck (only 2 left), and Baseball Left Chest Crewneck (15 in stock).
- *WITHOUT (search + get_stock)* — I need a small in this. Anything similar if it's gone?: Size S is sold out in the Davenport College Crewneck. Similar crewnecks available in S include the Jonathan Edwards College Crewneck, Grace Hopper College Crewneck, and Yale University Offside Crewneck; I’ve shown the options on the page.
- *WITH find_alternatives* — Is this available in XL? Otherwise show me something like it.: XL is sold out in the Champion Reverse Weave Hoodie 1. Here are a few similar hoodies available in XL: The Forest School Hoodie (12 in stock), Yale Uncle Hoodie (only 5 left), and Basic Hoodie Big Yale (only 2 left).
- *WITHOUT (search + get_stock)* — Is this available in XL? Otherwise show me something like it.: XL is sold out in the Champion Reverse Weave Hoodie. A similar navy option is the Basic Hoodie Big Yale, and only 2 are left in XL; other sizes available in the original are S, M, L, and XXL.
