---
draft: false
weight: 10
showAuthor: true
showDate: false
showWordCount: true
showReadingTime: true
date: 2026-01-02
---
# SOLID Principles in Object-Oriented Design
---
**SOLID** is an acronym for five core principles of [[Object Oriented Design]] popularized by Robert C. Martin (Uncle Bob). These principles act as a roadmap for developers to create software that is easy to maintain, scale, and understand over time.

| Acronym | Full Form                      | Key Concept                                                              |     |
| :------ | :----------------------------- | :----------------------------------------------------------------------- | --- |
| **S**   | **Single Responsibility**      | A class should have one reason to change.                                |     |
| **O**   | **Open-Close**                 | Software entities should be open for extension, closed for modification. |     |
| **L**   | **Liskov Substitution**        | Subtypes must be substitutable for their base types.                     |     |
| **I**   | **Interface Segregation**      | No client should be forced to depend on methods it does not use.         |     |
| **D**   | **Dependency Inversion (DIP)** | Depend on abstractions, not concretions.                                 |     |

---
## Single Responsibility Principle (SRP)
Single responsibility states:
> A class should have one and only one reason to change, meaning that class should have only one job.

For example, if we consider an application where we have to calculate sum of all the areas of the given collection of shapes (square or circle).

We can solve this problem with below approach.
### The Problematic Approach
Imagine you are creating `AreaCalculator` that handles both the math and the console output for calculating areas of all of the available shapes.

```java
public interface Shape {

}
public class Square implements Shape {

	public double length;
	public Square(double length) {
	
	this.length = length;
	
	}

}

public class Circle implements Shape {

	public double radius;
		
	public Circle(double radius) {
	
	this.radius = radius;
	
	}

}

public class AreaCalculator {

	private final Shape[] shapes;
		
	public AreaCalculator(Shape[] shapes) {
	
	this.shapes = shapes;

}

public double sum() {

	return Arrays.stream(shapes)
		.mapToDouble(shape -> {
			if (shape instanceof Circle) {
				return Math.PI * Math.pow(((Circle) shape).radius, 2);
			} else if (shape instanceof Square) {
				return Math.pow(((Square) shape).length, 2);
			}
			return 0.0;
			})
		.sum();
}  

	public void output() {
		System.out.println("Sum of areas of shape provided = " + sum());
	}
}

```

In this example there are two places where we are violating Single Responsibility Principle.
1. Method Sum :

This sum method has two responsibilities - Calculation of all the areas based on type of shape and Summing all the areas.

Problem: If we have to add new shape in the program then we will have to update this method which violates SRP.
2. Output:

Output of this class is strictly console based.

What if we need to change this output to non-console, something like JSON or HTML, again this class needs to be modified.
### Solution:
1. Create `Square` and `Circle` shapes but with added responsibility of calculating there own area.
```java
public interface Shape {
	double calculateArea();
}
```

```java
public class Circle implements Shape {

	public double radius;
	
	public Circle(double radius) {
		this.radius = radius;
	
	}
	
	@Override
	
	public double calculateArea() {
		return Math.PI * Math.pow(this.radius, 2);
	}

}

```

```java
public class Square implements Shape {

	public double length;
	
	public Square(double length) {
		this.length = length;
	}
	
	@Override
	public double calculateArea() {
		return Math.pow(this.length, 2);
	}
}

```

  

1. With the delegation of area calculation above the `AreaCalculator` class will have just one responsibility of calculating the sum of all the areas, where each area will be provided by the shape class itself.

```java
public class AreaCalculator {
	private final Shape[] shapes;
	public AreaCalculator(Shape[] shapes) {
		this.shapes = shapes;
	}
	
	public double sum() {
		return Arrays.stream(shapes)
			.mapToDouble(Shape::calculateArea)
			.sum();
	}
}

```

2. Now the question arises, what about output.

Output we will be handling differently using different class called `AreaCalculatorOutputter` whose sole responsibility will be to create output in different format by invoking `sum` method in `AreaCalculator`.

```java
public class AreaCalculatorOutputter {

	private final AreaCalculator areaCalculator;

	public AreaCalculatorOutputter(AreaCalculator areaCalculator) {
		this.areaCalculator = areaCalculator;
	}

	public String jsonOutput() {
	
		double sum = this.areaCalculator.sum();
		
		return String.format("{\"total_area\": \"Total area for the shapes provided is : [%s]\"}", sum);
	
	}

	public String htmlOutput() {
	
		double sum = this.areaCalculator.sum();
		
		return String.format("<div>Total area for the shapes provided is : [%s]</div>", sum);
	
	}

}

```
## Open-Closed Principle (OCP)
Open Close principle states:
> The class should be open for extension but closed for modification.

What does this means?
In the original `AreaCalculator`, adding a new shape (like a Triangle) requires modifying the `sum()` method with a new `if` statement. This makes the class fragile.
```java
public class AreaCalculator {

	private final Shape[] shapes;
	public AreaCalculator(Shape[] shapes) {
		this.shapes = shapes;
	}
	
	  
	
	public double sum() {
	
		return Arrays.stream(shapes)
			.mapToDouble(shape -> {
		
				if (shape instanceof Circle) {
					return Math.PI * Math.pow(((Circle) shape).radius, 2);
				} else if (shape instanceof Square) {
					return Math.pow(((Square) shape).length, 2);
				}
				return 0.0;
				})
				.sum();
	}
	
	  
	
	public void output() {
		System.out.println("Sum of areas of shape provided = " + sum());
	}
}

```

In this case what will happen?
If you want to add another Triangle shape in the array it won’t calculate the area unless you change the code to have 3rd scenario.

**But about pentagon or a rhombus or a parallelogram?**

Irrespective of whatever number of shapes you will add to the collection the class has to be modified.

This means this class is definitely not open for extension and absolutely not close to modification.

The Solution
By using the `Shape` interface with a `calculateArea()` method, the `AreaCalculator` becomes **closed to modification**. You can add any number of new shapes without changing the calculator's code.
```java
public class AreaCalculator {

	private final Shape[] shapes;
	public AreaCalculator(Shape[] shapes) {
		this.shapes = shapes;
	}
	
	  
	
	public double sum() {
		return Arrays.stream(shapes)
			.mapToDouble(Shape::calculateArea)
			.sum();
	}
}

```
Now irrespective of what shape you add to the collection, if it is of type shape the total area will be calculated.
## Liskov Substitution
Liskov Substitution principle states that
> Objects of a superclass (parent) should be replaceable with objects of its subclasses (children) without breaking the application.

What does this means?
This means when inheriting code from parent, the child class must also honor the behavior and expectations of parent.

For example
`[The Classic Violation: Square vs. Rectangle]` If we create Rectangle and Square class where Square extends Rectangle.

```java
public class Rectangle {

	private int width;
	private int length;
	
	public int getWidth() {
		return width;
	}
	
	public void setWidth(int width) {
		this.width = width;
	}
	
	public int getLength() {
		return length;
	}
	
	public void setLength(int length) {
		this.length = length;
	}
	
	public int getArea() {
		return this.width * this.length;
	}
}

public class Square extends Rectangle {
	@Override
	public void setWidth(int width) {
		super.setWidth(width);
		super.setLength(width);
	}
	
	@Override
	public void setLength(int length) {
		super.setLength(length);
		super.setWidth(length);
	}
}

```

In this case as long as `Rectangle` is used everything is fine.
But in cases where `Rectangle` refers `Square` and when you calculate area the answer can be wrong.
Look at the below example.
```java
public class Runner {

	public static void main(String[] args) {
		Rectangle r = new Rectangle();
		r.setLength(10);
		r.setWidth(5);
		
		assert 50 == r.getArea() : "Area should be 50";
		
		Rectangle s = new Square();
		s.setWidth(5);
		s.setLength(10);
		
		assert 50 == s.getArea() : "Area should be 50";
		
		System.out.println("Completed");
	
	}

}

```

In the above example if you run the first `Rectangle` will give you correct area whereas the second `Rectangle` which represents `Square` will have result in wrong output because it violates `LSP`.

The Solution:
Instead of forced inheritance, treat `Square` and `Rectangle` as separate implementations of a `Shape` interface to ensure `calculateArea(Shape s)` works predictably for both.

```java
public interface Shape {
	double getArea();
}

public class Rectangle implements Shape {

	private int length;
	private int width;
	
	public int getLength() {
		return length;
	}
	
	  
	
	public void setLength(int length) {
		this.length = length;
	}
	
	public int getWidth() {
		return width;
	}
	
	public void setWidth(int width) {
		this.width = width;
	}
	
	@Override
	public double getArea() {
		return 0;
	}
}

  

public class Square implements Shape {
	private int side;
	
	public int getSide() {
		return side;
	}
	
	public void setSide(int side) {
		this.side = side;
	}
	
	@Override
	public double getArea() {
		return Math.pow(this.side, 2);
	}
}

  

public class Runner {

	public static void main(String[] args) {
		Rectangle r = new Rectangle();
		r.setLength(10);
		r.setWidth(5);
		
		assert 50 == calculateArea(r) : "Area should be 50";
		
		Square s = new Square();
		s.setSide(10);
		
		assert 100 == calculateArea(s) : "Area should be 100";
		
		System.out.println("All completed");
	}

	private static double calculateArea(Shape s) {
		return s.getArea();
	}
}

```

## Interface Segregation
The interface segregation principle states:
> A class should never be forced to implement methods it doesn’t use.

What does it mean?
We should always try to avoid “`FAT INTERFACE PROBLEM`”, meaning, we should not create interface that does everything, and the result of that all implementors are forced to implement methods which are not of there use.

For example:
```java
public interface SmartDevice {
	void print();
	void scan();
	void fax();
}

  

public class BasicPrinter implements SmartDevice {
	@Override
	public void print() {
		System.out.println("The printer is Printing...");
	}
	
	@Override
	public void scan() {
		throw new UnsupportedOperationException("This operation is not supported in Basic Printer");
	}

  

	@Override
	public void fax() {
		throw new UnsupportedOperationException("This operation is not supported in Basic Printer");
	}

}

  

public class NewAgePrinter implements SmartDevice {

	@Override
	public void print() {
		System.out.println("The printer is printing...");
	}

	@Override
	public void scan() {
		System.out.println("The printer is scanning...");
	}

	@Override
	public void fax() {
	System.out.println("The printer is sending the fax...");
	}

}

```

In the above example the SmartDevice interface is the best example of Fat Interface Problem.

This class includes everything, it does not values the fact that there might be printer instance which cannot send fax or do scanning, as in case of BasicPrinter.

This kind of implementation is prone to errors like:
- Confusion: A developer using BasicPrinter might think it works for Scanning and Faxing, due to autocomplete feature of many modern IDEs. But during the runtime it will come to know that these features are not supported in BasicPrinter. This might lead to crash during runtime as well.
- Rigidity: If there is a change in Fax method signature, the BasicPrinter class also needs to be changed even though it does not work do Fax.
- Deployment issues: in large systems changing a fat interface forces a re-compilation of every class that uses it, even if they don’t care about the specific method you changed.

The Solution:
Break the interface into smaller, specific contracts like `Printer`, `Scanner`, and `FaxMachine`.
```java
public interface Printer {

	void print();

}

public interface Scanner {

	void scan();

}

public interface FaxMachine {

	void fax();

}

  

public class BasicPrinter implements Printer {

	@Override
	public void print() {
	
		System.out.println("The printer is printing...");
	
	}

}

public class NewAgePrinter implements Printer, Scanner, FaxMachine{

	@Override
	public void fax() {
		System.out.println("Machine is sending fax...");
	}

	@Override
	public void print() {
		System.out.println("Printer is printing...");
	}

	@Override
	public void scan() {
		System.out.println("Scanner is scanning...");
	}
}

```

In this implementation all the classes implements exactly what they need to work with.

the BasicPrinter only prints stuff and the NewAgePrinter does all the work like printing, scanning and sending fax.
## Dependency Inversion
Dependency Inversion states:
> 1. High-level modules should not import anything from low-level modules. Both should depend on abstractions (e.g., interfaces).
> 2. Abstractions should not depend on details. Details (concrete implementations) should depend on abstractions.

What does this means?
Imagine you are building a NotificationManager, for now you want to send email.

```java

public class EmailSender {

	public void send(String message) {
		System.out.println("Sending email : " + message);
	}

}

public class NotificationManager {
	private EmailSender emailSender = new EmailSender();
	public void notify(String message) {
		emailSender.send(message);
	}
}
```

In this there are three major problems:
- Rigid: NotificationManager is very rigid in nature, if you want to send SMS instead of email, you have to change the class to do it.

- Untestable: NotificationManager is not testable on it own. If the functionality of notification manager has to be tested then the email must be sent to do it.

- Violates OCP: If there is a requirement change and user wants to add new notification type the existing code must be modified.

Solution:
```java

public interface MessageService {
	void sendMessage(String message);
}

public class EmailService implements MessageService {
	@Override
	public void sendMessage(String message) {
		System.out.println("Sending message: " + message + ", via email...");
	}

}

public class SmsService implements MessageService {
	@Override
	public void sendMessage(String message) {
	System.out.println("Sending message: " + message + ", via SMS.");
	}
}

public class NotificationManager {
	private final MessageService messageService;

	public NotificationManager(MessageService messageService) {
		this.messageService = messageService;
	}

	public void notify(String message) {
	this.messageService.sendMessage(message);
	}
}
```

With this now NotificationManager doesn’t directly depend on any kind of implementation rather it takes the contract and execute type of implementation whatever is provided at the runtime.