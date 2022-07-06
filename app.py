from tkinter import *
from tkinter import messagebox
import pandas as pd
pd.options.mode.chained_assignment = None

CATEGORIES = ["Groceries", "Eating Out", "Fun", "Medications", "Gas/Car", "Subscriptions", "Bills", "Miscellaneous",
              "Income", "Savings", "CC Payment"]

# ---------------------------- FUNCTIONS ------------------------------- #


# add new merchants to lookup table
def add_merchant(pay_df):
    new_lookup = pay_df[pay_df.Note.isna()]['MERCHANT']
    new_lookup.drop_duplicates(inplace=True)
    merchants = new_lookup.tolist()
    entries = []
    cats = []
    notes = []

    # pop up message
    top = Toplevel()
    top.minsize(width=200, height=100)
    top.config(padx=20, pady=20)
    top.title("Categories Added")

    head_label = Label(top, text=f"There are {len(merchants)} merchants that need to be added to the Categories Lookup "
                                 f"file")
    head_label.grid(column=1, columnspan=3, row=0, pady=5)

    # create entry boxes for each merchant and append them to their respective lists to be able to retrieve values
    # later
    for i in range(len(merchants)):
        entries.append({"merchant": merchants[i]})
        Label(top, text=f"{merchants[i]}").grid(column=0, row=i + 1)
        Label(top, text="Category: ", width=15, anchor="e").grid(column=1, row=i + 1)
        cats.append(StringVar(top))
        cats[i].set(CATEGORIES[0])
        OptionMenu(top, cats[i], *CATEGORIES).grid(column=2, row=i + 1)
        Label(top, text="Note: ").grid(column=3, row=i + 1)
        notes.append(Entry(top, width=25))
        notes[i].insert(0, merchants[i])
        notes[i].grid(column=4, row=i + 1)

    # run on confirm button press, updates the category_lookup csv then closes the popup
    def update_and_close():
        for w in range(len(entries)):
            entries[w]["note"] = notes[w].get()
            entries[w]["category"] = cats[w].get()
        df = pd.DataFrame(entries)
        df.to_csv('category_lookup.csv', mode='a', header=False, index=False)
        top.destroy()

    confirm = Button(top, text="Confirm", command=update_and_close)
    confirm.grid(column=2, row=20, pady=5)

    root.wait_window(top)


# function to merge dfs
def fill_in_cat(pay_df):
    cat_lookup = pd.read_csv(cl_path.get())
    if "Note" in pay_df.columns:
        pay_df.drop(columns=["Note", "Category"], inplace=True)
    df = pd.merge(pay_df, cat_lookup, on="MERCHANT", how='left')
    return df


# text cleaner
def text_clean(pay_df):
    for _ in range(4):
        to_replace = [" ..$", " #", "\d+", "MENOMONIE", "Inc g.co/helppay#CA", " --", "Amzn.com/billWA",
                      "(?<=DOORDASH) .*", "(?<=AMZN Mktp).*", " $", "  $", " EAU CLAIRE", "ACH PYMT", "^PC", "^PPD",
                      ", Inc.$", "^ "]
        pay_df.MERCHANT.replace(to_replace, "", regex=True, inplace=True)
        wm_replace = ["WM SUPERCENTER", "WALMART.COM AA", "WALMART.COM", "WAL-MART"]
        pay_df.MERCHANT.replace(wm_replace, "WALMART", inplace=True)

    # proper case
    pay_df.MERCHANT = pay_df.MERCHANT.str.title()

    return pay_df


# ---------------------------- CC CLEANER ------------------------------- #
def cc_cleaner():
    cc_df = pd.read_csv(cc_path.get())

    # drop unnecessary columns
    cc_df.drop(columns=["POSTING DATE", "MERCHANT CITY", "MERCHANT ZIP", "REFERENCE NUMBER", "DEBIT/CREDIT FLAG",
                        "SIMCC CODE", "TRANSACTION CATEGORY", "TRANSACTION CATEGORY DESCRIPTION"], inplace=True)

    # rename existing columns
    cc_df.rename(columns={"ACCOUNT TYPE": "Card", "TRANSACTION DATE": "Date", "BILLING AMOUNT": "Amount"}, inplace=True)

    # insert missing required columns
    cc_df["Period"] = current_per.get()

    # drop payment rows
    cc_df = cc_df[cc_df.MERCHANT != "PAYMENT RECEIVED -THANKYOU"]

    # take absolute value of amount
    cc_df.Amount = abs(cc_df.Amount)

    # clean up MERCHANT column for lookup
    cc_df = text_clean(cc_df)

    # proper case
    cc_df.Card = cc_df.Card.str.title()

    # fill in Category and Note with existing data
    cc_df = fill_in_cat(cc_df)

    # prompts user to enter missing data
    null_cats = cc_df[cc_df.Note.isna()].shape[0]
    if null_cats > 0:
        add_merchant(cc_df)
        cc_df = fill_in_cat(cc_df)

    # reorganize columns
    cc_df = cc_df[['Period', 'Date', 'Card', 'Category', 'Amount', 'Note']]

    # export final csv
    cc_df.to_csv(clean_path.get(), mode='a', header=False, index=False)

    # confirmation message
    messagebox.showinfo(title="Confirmation", message="Upload complete.")

    # disable button so the file isn't accidentally re-cleaned
    run_cc.config(state=DISABLED)


# ---------------------------- DC CLEANER ------------------------------- #


def dc_cleaner():
    dc_df = pd.read_csv(dc_path.get())

    # drop unnecessary columns
    dc_df.drop(columns=["CURRENCY", "TRANSACTION REFERENCE NUMBER", "FI TRANSACTION REFERENCE", "CREDIT/DEBIT",
                        "ORIGINAL AMOUNT"], inplace=True)

    # rename existing columns
    dc_df.rename(columns={"TYPE": "Card", "POSTED DATE": "Date", "AMOUNT": "Amount", "DESCRIPTION": "MERCHANT"},
                 inplace=True)

    # insert missing required columns
    dc_df["Period"] = current_per.get()

    # take absolute value of amount
    dc_df.Amount = abs(dc_df.Amount)

    # map the values of Card to the standardized values
    dc_df.Card = dc_df.Card.map({"DDA Deposit": "Income", "DDA Debit": "Debit Card"})

    text_clean(dc_df)
    dc_df = fill_in_cat(dc_df)

    # prompts user to enter missing data
    null_cats = dc_df[dc_df.Note.isna()].shape[0]
    if null_cats > 0:
        add_merchant(dc_df)
        dc_df = fill_in_cat(dc_df)

    # reorganize columns
    dc_df = dc_df[['Period', 'Date', 'Card', 'Category', 'Amount', 'Note']]

    # export final csv
    dc_df.to_csv(clean_path.get(), mode='a', header=False, index=False)

    # confirmation message
    messagebox.showinfo(title="Confirmation", message="Upload complete.")

    # disable the button so the file isn't accidentally re-cleaned
    run_dc.config(state=DISABLED)


# ---------------------------- UI SETUP ------------------------------- #
root = Tk()
root.title("Transaction Upload")
root.minsize(width=400, height=50)
root.config(padx=20, pady=20)

cc_path_label = Label(text="CC Transaction File Path:")
cc_path_label.grid(column=0, columnspan=2, row=0, pady=5)
cc_path = Entry(width=40)
cc_path.insert(0, "cc.csv")
cc_path.grid(column=2, columnspan=3, row=0)

dc_path_label = Label(text="DC Transaction File Path:")
dc_path_label.grid(column=0, columnspan=2, row=1, pady=5)
dc_path = Entry(width=40)
dc_path.insert(0, "dc.csv")
dc_path.grid(column=2, columnspan=3, row=1)

cl_path_label = Label(text="Category Lookup File Path:")
cl_path_label.grid(column=0, columnspan=2, row=2, pady=5)
cl_path = Entry(width=40)
cl_path.insert(0, "category_lookup.csv")
cl_path.grid(column=2, columnspan=3, row=2)

clean_path_label = Label(text="Clean Data File Path:")
clean_path_label.grid(column=0, columnspan=2, row=3, pady=5)
clean_path = Entry(width=40)
clean_path.insert(0, "clean_data.csv")
clean_path.grid(column=2, columnspan=3, row=3)

current_per_label = Label(text="Current Period: ")
current_per_label.grid(column=0, columnspan=2, row=4, pady=5)
current_per = Entry(width=40)
current_per.grid(column=2, columnspan=3, row=4)

run_cc = Button(text="Clean CC File", width=15, command=cc_cleaner)
run_cc.grid(column=1, row=5, pady=30)

run_dc = Button(text="Clean DC File", width=15, command=dc_cleaner)
run_dc.grid(column=4, row=5)

root.mainloop()
