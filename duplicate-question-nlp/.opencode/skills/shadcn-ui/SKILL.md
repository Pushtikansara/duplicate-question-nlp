---
name: shadcn-ui
description: Use when building UIs with shadcn/ui components. Covers component usage, customization, theming, and best practices.
---

# shadcn/ui Skill

## Instructions

1. Initialize shadcn/ui in your project: `npx shadcn@latest init`. This sets up the components directory, theme configuration, and CSS variables.
2. Choose a base color scheme during init: Neutral, Gray, Zinc, Stone, Slate, or custom. This generates the CSS variable values in `globals.css`.
3. Add individual components as needed: `npx shadcn@latest add button card dialog form input select table`.
4. Components are copied directly into your project's `components/ui` directory — you own the code and can modify it freely.
5. Customize the theme by editing CSS variables in `globals.css`: `--primary`, `--secondary`, `--accent`, `--background`, `--foreground`, `--muted`, `--border`, `--ring`.
6. Use the `cn()` utility (provided by default) for class merging: `cn("base-class", conditional && "extra-class")`.
7. Leverage Radix UI primitives that shadcn/ui wraps: Dialog, DropdownMenu, Popover, Tooltip, Select, Tabs, etc. follow the Radix accessibility and behavior model.
8. Compose complex UIs by combining shadcn/ui components: a Form with Input, Select, Checkbox, and Button within a Card.
9. Customize component variants using `cva` (Class Variance Authority) for extending component styles.
10. Override component styles by modifying the component files directly in `components/ui/`. You have full control.
11. Use the `asChild` prop (from Radix's Slot) to compose components: `<Button asChild><Link href="/">Home</Link></Button>`.
12. Follow the form patterns using `react-hook-form` with `zod` validation, which shadcn/ui Form components are designed for.
13. Use `useTheme` from `next-themes` for dark mode toggling — shadcn/ui init sets this up automatically.
14. Keep the `components/ui` directory clean — only add components you are actively using.
15. Update individual components when upgrading shadcn/ui: `npx shadcn@latest add -o button` (the `-o` flag overwrites existing).
16. Use the `--radius` CSS variable for consistent border-radius theming across all components.
17. Leverage Tailwind's `dark:` variants in shadcn/ui components — the CSS variables automatically switch based on the dark mode class.
18. Build page-specific layouts by composing shadcn/ui layout components: Container, Separator, ScrollArea, AspectRatio.
19. Extend components with additional props using TypeScript interfaces — shadcn/ui components are typed.
20. Use shadcn/ui's Chart component (built on Recharts) for accessible, themed data visualizations.

## Examples

### Button Variants
```tsx
import { Button } from "@/components/ui/button";

export function ButtonDemo() {
  return (
    <div className="flex flex-wrap gap-4">
      <Button>Default</Button>
      <Button variant="secondary">Secondary</Button>
      <Button variant="destructive">Destructive</Button>
      <Button variant="outline">Outline</Button>
      <Button variant="ghost">Ghost</Button>
      <Button variant="link">Link</Button>
      <Button size="sm">Small</Button>
      <Button size="lg">Large</Button>
      <Button size="icon"><SearchIcon /></Button>
      <Button disabled>Disabled</Button>
      <Button asChild>
        <a href="/dashboard">Link as Button</a>
      </Button>
    </div>
  );
}
```

### Form with Validation
```tsx
"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { toast } from "@/components/ui/use-toast";

const formSchema = z.object({
  username: z.string().min(2).max(50),
  email: z.string().email(),
  role: z.enum(["user", "admin", "editor"]),
});

export function ProfileForm() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: "",
      email: "",
      role: "user",
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    toast({ title: "Form submitted", description: JSON.stringify(values) });
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="johndoe" {...field} />
              </FormControl>
              <FormDescription>Your public display name.</FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="john@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />
        <FormField
          control={form.control}
          name="role"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Role</FormLabel>
              <Select onValueChange={field.onChange} defaultValue={field.value}>
                <FormControl>
                  <SelectTrigger>
                    <SelectValue placeholder="Select a role" />
                  </SelectTrigger>
                </FormControl>
                <SelectContent>
                  <SelectItem value="user">User</SelectItem>
                  <SelectItem value="admin">Admin</SelectItem>
                  <SelectItem value="editor">Editor</SelectItem>
                </SelectContent>
              </Select>
              <FormMessage />
            </FormItem>
          )}
        />
        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

### Dialog with Form
```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

export function EditDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline">Edit Profile</Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-[425px]">
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
          <DialogDescription>
            Make changes to your profile here. Click save when done.
          </DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 py-4">
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="name" className="text-right">Name</Label>
            <Input id="name" defaultValue="John Doe" className="col-span-3" />
          </div>
          <div className="grid grid-cols-4 items-center gap-4">
            <Label htmlFor="bio" className="text-right">Bio</Label>
            <Input id="bio" defaultValue="Developer" className="col-span-3" />
          </div>
        </div>
        <DialogFooter>
          <Button type="submit">Save Changes</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Data Table
```tsx
"use client";

import {
  ColumnDef,
  flexRender,
  getCoreRowModel,
  useReactTable,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
} from "@tanstack/react-table";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface Payment {
  id: string;
  amount: number;
  status: "pending" | "processing" | "success" | "failed";
  email: string;
}

const columns: ColumnDef<Payment>[] = [
  { accessorKey: "id", header: "ID" },
  { accessorKey: "amount", header: "Amount",
    cell: ({ row }) => `$${row.getValue("amount")}`,
  },
  { accessorKey: "status", header: "Status" },
  { accessorKey: "email", header: "Email" },
];

export function DataTableDemo({ data }: { data: Payment[] }) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
  });

  return (
    <div className="space-y-4">
      <Input
        placeholder="Filter emails..."
        value={(table.getColumn("email")?.getFilterValue() as string) ?? ""}
        onChange={(e) => table.getColumn("email")?.setFilterValue(e.target.value)}
        className="max-w-sm"
      />
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((group) => (
              <TableRow key={group.id}>
                {group.headers.map((header) => (
                  <TableHead key={header.id}>
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {table.getRowModel().rows.map((row) => (
              <TableRow key={row.id}>
                {row.getVisibleCells().map((cell) => (
                  <TableCell key={cell.id}>
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
      <div className="flex items-center justify-end space-x-2">
        <Button variant="outline" size="sm" onClick={() => table.previousPage()} disabled={!table.getCanPreviousPage()}>
          Previous
        </Button>
        <Button variant="outline" size="sm" onClick={() => table.nextPage()} disabled={!table.getCanNextPage()}>
          Next
        </Button>
      </div>
    </div>
  );
}
```

### Custom Theme
```css
/* globals.css */
@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 240 10% 3.9%;
    --card: 0 0% 100%;
    --card-foreground: 240 10% 3.9%;
    --popover: 0 0% 100%;
    --popover-foreground: 240 10% 3.9%;
    --primary: 240 5.9% 10%;
    --primary-foreground: 0 0% 98%;
    --secondary: 240 4.8% 95.9%;
    --secondary-foreground: 240 5.9% 10%;
    --muted: 240 4.8% 95.9%;
    --muted-foreground: 240 3.8% 46.1%;
    --accent: 240 4.8% 95.9%;
    --accent-foreground: 240 5.9% 10%;
    --destructive: 0 84.2% 60.2%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 5.9% 90%;
    --input: 240 5.9% 90%;
    --ring: 240 5.9% 10%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 240 10% 3.9%;
    --foreground: 0 0% 98%;
    --card: 240 10% 3.9%;
    --card-foreground: 0 0% 98%;
    --popover: 240 10% 3.9%;
    --popover-foreground: 0 0% 98%;
    --primary: 0 0% 98%;
    --primary-foreground: 240 5.9% 10%;
    --secondary: 240 3.7% 15.9%;
    --secondary-foreground: 0 0% 98%;
    --muted: 240 3.7% 15.9%;
    --muted-foreground: 240 5% 64.9%;
    --accent: 240 3.7% 15.9%;
    --accent-foreground: 0 0% 98%;
    --destructive: 0 62.8% 30.6%;
    --destructive-foreground: 0 0% 98%;
    --border: 240 3.7% 15.9%;
    --input: 240 3.7% 15.9%;
    --ring: 240 4.9% 83.9%;
  }
}
```

## Best Practices

- Only add components you use. shadcn/ui copies files into your project, so unused components are just dead code.
- Customize component styles by editing the component files directly. This is the intended workflow — you own the code.
- Use the `cn()` helper consistently for all class merging. Install `tailwind-merge` and `clsx` if not already present.
- Keep the `components/ui` directory structure flat. Do not nest UI components in subdirectories.
- Use composition over configuration. Combine primitive components (Dialog + Form + Button) rather than looking for a single complex component.
- Set up `@/components` path alias in `tsconfig.json` and `vite.config.ts` for clean imports: `import { Button } from "@/components/ui/button"`.
- Use `asChild` liberally for polymorphic components. It preserves accessibility and styling while changing the underlying element.
- Follow the form patterns exactly as documented. The `react-hook-form` + `zod` + `FormField` pattern is well-tested.
- Use `next-themes` ThemeProvider for dark mode. Wrap your app with it and use `useTheme` to toggle.
- Keep CSS variables in `globals.css` using the HSL format shadcn/ui generates. Do not switch to hex or rgb without updating all components.
- Use the `--radius` variable consistently. shadcn/ui components reference it for border-radius.
- Update shadcn/ui components with `npx shadcn@latest add -o <component>` when new versions are released.
- Review the diff when updating components. Your customizations may conflict with upstream changes.
- Use `useToast` from shadcn/ui's toast component for notifications. It provides a clean, accessible toast system.
- For server components, use shadcn/ui components that do not require client-side interactivity (Card, Badge, Table layout).
- Keep custom component variants in a separate `components/ui/variants.ts` file if they are shared across multiple components.
- Use React Hook Form's `Controller` for custom controlled components not covered by shadcn/ui's FormControl.
- Document custom component modifications in a README within `components/ui/` to track deviations from upstream.

## Common Mistakes

- Adding all shadcn/ui components at once during initialization instead of adding them as needed.
- Modifying CSS variables without understanding the HSL format — shadcn/ui uses HSL with hue, saturation, lightness channels.
- Overriding component styles in `globals.css` instead of editing the component file directly.
- Not using the `asChild` prop for link buttons, causing `<button>` inside `<a>` nesting.
- Forgetting to wrap the app with `ThemeProvider` from `next-themes`, causing dark mode issues.
- Using shadcn/ui components in Server Components when they require client-side interactivity (dialogs, dropdowns, forms).
- Not using `"use client"` directive for components that use React hooks (`useState`, `useEffect`, `useForm`).
- Over-customizing the `cn()` utility — it should merge Tailwind classes, not add custom logic.
- Using shadcn/ui's old `useToast` import path after upgrading to the newer Toast pattern.
- Hardcoding colors instead of using CSS variables, breaking dark mode compatibility.
- Modifying the `components/ui` index barrel exports, causing import resolution errors.
- Using shadcn/ui components without Tailwind CSS properly configured and purging working.
- Nesting `FormField` inside `FormItem` incorrectly — the render prop pattern must be followed exactly.
- Not installing `@hookform/resolvers` for zod integration with react-hook-form.
- Using `zod` schemas without proper error messages, resulting in generic form validation feedback.
- Creating custom components that duplicate shadcn/ui primitives instead of composing them.
- Upgrading shadcn/ui without checking for breaking changes in Radix UI or underlying dependencies.

## Libraries and Tools

- **shadcn/ui**: The core component collection. Built on Radix UI primitives.
- **Radix UI**: Unstyled, accessible React primitives that shadcn/ui wraps.
- **TailwindCSS**: Utility-first CSS framework. Required by shadcn/ui.
- **clsx + tailwind-merge**: Class merging utilities used by the `cn()` helper.
- **react-hook-form**: Performant form library with minimal re-renders.
- **@hookform/resolvers**: Validation resolver integration for react-hook-form.
- **zod**: TypeScript-first schema validation library.
- **@tanstack/react-table**: Headless table library used by shadcn/ui's Table and DataTable patterns.
- **next-themes**: Theme provider for Next.js with dark mode support.
- **Recharts**: Composable chart library used by shadcn/ui's Chart component.
- **lucide-react**: Icon library. shadcn/ui uses Lucide icons in its examples.
- **date-fns**: Date utility library for formatting and manipulation.
- **react-day-picker**: Date picker component used by shadcn/ui's Calendar and DatePicker.
- **vaul**: Drawer component by shadcn/ui for mobile-friendly bottom sheets.
- **cmdk**: Command menu component used by shadcn/ui's Command and Combobox.
- **input-otp**: OTP input component for verification codes.
- **embla-carousel**: Carousel library used by shadcn/ui's Carousel component.
- **recharts**: Charting library used by shadcn/ui's Chart component.
- **sonner**: Toast library used by shadcn/ui's Sonner-based toast implementation.
- **@radix-ui/react-select, react-dropdown-menu, react-dialog, etc.**: Individual Radix packages used by specific components.

## Design Principles

1. **Own Your Code**: shadcn/ui is not a dependency — it is a collection of source files copied into your project. You have complete control and can modify every aspect.
2. **Copy-Paste Components**: Components are designed to be copied and pasted into your project. They are not published to npm as a single package.
3. **Composition over Configuration**: Build complex interfaces by composing simple, focused primitives. Do not create monolithic mega-components.
4. **Accessibility by Default**: All components are built on Radix UI primitives, which follow WAI-ARIA standards. Accessibility is not an afterthought.
5. **Themeable via CSS Variables**: All design tokens are defined as CSS variables (in HSL format). Changing the variables changes the entire visual system.
6. **Variants over Props**: Use CVA (Class Variance Authority) for component variations (size, variant, color) rather than complex prop logic.
7. **Progressive Enhancement**: Components work without JavaScript where possible (buttons, links, form elements) and enhance with JS for richer interactions.
8. **Consistency through Convention**: Follow established patterns (Forms with react-hook-form, Tables with tanstack-table) for consistency across the project.

## Coding Standards

- All components in `components/ui/` must be strictly presentational. Business logic belongs in feature components.
- Use `"use client"` only when necessary (components using hooks, event handlers, browser APIs).
- Export components as named exports, not default exports: `export function Button()`.
- Use the `cn()` utility for all conditional class names. Never use template literals for class merging.
- Define component variants using `cva` from `class-variance-authority`: `export const buttonVariants = cva("base-classes", { variants: { variant: {...}, size: {...} } })`.
- Use TypeScript throughout. Define explicit prop interfaces extending `React.HTMLAttributes` or Radix props.
- Use `forwardRef` for all components that need to pass refs to underlying DOM elements.
- Use `asChild` via Radix's `Slot` for polymorphic components: `import { Slot } from "@radix-ui/react-slot"`.
- Use `React.ComponentPropsWithoutRef<typeof RadixComponent>` to extend Radix component props.
- Keep component files focused: one component per file, with a matching `index.ts` barrel export.
- Use controlled components with `value` and `onChange` for form fields, not uncontrolled refs.
- Use `useId()` for generating unique IDs for ARIA attributes within components.
- All interactive elements must have focus styles: `focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2`.
- CSS variables must follow the shadcn/ui naming convention: `--component-property` (e.g., `--card`, `--card-foreground`, `--primary`, `--primary-foreground`).
- Color values must be in HSL format: `--primary: 240 5.9% 10%` (not hex or rgb).
- Responsive variants should be applied via Tailwind's responsive prefixes, not JS breakpoints.
- Use `@layer base { ... }` for defining base CSS variable values and global resets.

